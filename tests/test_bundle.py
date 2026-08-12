from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
sys.path.insert(0, str(ROOT / "scripts"))
from workflow_runner import attach_behavior_spec, attach_final_brief, begin_phase, can_handoff, checkpoint, new_state, record_review  # noqa: E402
from workbench_adapter import detect, publish_local  # noqa: E402


class BundleTests(unittest.TestCase):
    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([PYTHON, str(ROOT / "scripts" / name), *args], cwd=ROOT, text=True, capture_output=True)

    def test_bundle_validates(self):
        result = self.run_script("validate_bundle.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_skill_starts_with_qa_and_mode_routing(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        for phrase in ["What do you want to build or improve?", "Prototype", "Hackathon", "Indie App", "SaaS", "Startup", "wait for explicit confirmation", "Expo", "Flutter", "SwiftUI", "Next.js", "market probe", "Mode revisit"]:
            self.assertIn(phrase, skill)

    def test_schemas_are_valid_json(self):
        for path in (ROOT / "schemas").glob("*.json"):
            with self.subTest(path=path):
                json.loads(path.read_text())

    def test_init_project_creates_resumeable_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_script("init_project.py", "Test App", "--directory", directory, "--mode", "hackathon")
            self.assertEqual(result.returncode, 0, result.stderr)
            state = Path(directory) / ".product-studio" / "project.yaml"
            self.assertTrue(state.exists())
            self.assertIn("mode: hackathon", state.read_text())
            self.assertIn("house_rules:", state.read_text())
            self.assertIn("current_phase: intake", state.read_text())
            self.assertIn("phases:", state.read_text())
            self.assertIn("approval_status: pending", state.read_text())
            self.assertIn("last_checkpoint: null", state.read_text())
            self.assertIn("final_planning:", state.read_text())
            self.assertTrue((state.parent / "artifacts").is_dir())

    def test_install_and_uninstall_are_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            result = self.run_script("install.py", "--target", "agents", "--destination", str(destination))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((destination / "product-studio" / "SKILL.md").exists())
            self.assertTrue((destination / "product-studio" / "templates" / "mvp-build-plan.md").exists())
            self.assertTrue((destination / "product-studio" / "schemas" / "project.schema.json").exists())
            for name in ("product-recheck", "workflow-init", "engineering-cycle"):
                self.assertTrue((destination / name / "SKILL.md").exists(), name)
            self.assertTrue((destination / "workflow-init" / "scripts" / "init.sh").exists())
            self.assertTrue((destination / "engineering-cycle" / "references" / "review.md").exists())
            # workflow-init and engineering-cycle are self-contained; packaging the
            # shared planning resources beside them would add dirs they never name.
            for name in ("workflow-init", "engineering-cycle"):
                self.assertFalse((destination / name / "pattern-library").exists(), name)
                self.assertFalse((destination / name / "schemas").exists(), name)
            result = self.run_script("install.py", "--target", "agents", "--destination", str(destination), "--uninstall")
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("product-studio", "product-recheck", "workflow-init", "engineering-cycle"):
                self.assertFalse((destination / name).exists(), name)

    def test_workflow_init_self_check_passes(self):
        script = ROOT / "skills" / "workflow-init" / "scripts" / "init.sh"
        result = subprocess.run(["bash", str(script), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CHECK OK", result.stdout)

    def test_intake_extracts_intent_rather_than_collecting_answers(self):
        # Everything downstream — mode, platform, behaviors, the whole Behavior Spec —
        # inherits a misread goal, and no amount of ambiguity sweeping later catches one
        # that was wrong in the first sentence. These are the mechanics that make the
        # difference checkable rather than a matter of tone.
        # normalize wrapping — these are prose files, so a phrase may straddle a line break
        flat = lambda path: " ".join((ROOT / path).read_text().lower().split())
        skill = flat("skills/product-studio/SKILL.md")
        protocol = flat("skills/product-studio/references/qa-session.md")
        for phrase in ["hypothesis", "confidence", "one question at a time", "out of scope"]:
            self.assertIn(phrase, skill, phrase)
        for phrase in ["hypothesis:", "confidence:", "guess:", "out of scope",
                       "whatever you think", "justify this to anyone",
                       # the stop condition must be a test someone can apply, not a feeling
                       "next three questions"]:
            self.assertIn(phrase, protocol, phrase)

    def test_engineering_module_refuses_to_write_anything_without_its_sibling_skill(self):
        # workflow-init copied out on its own has no engineering-cycle beside it. The
        # copy must fail before touching the project, not halfway through the core
        # files and before the CLAUDE.md bridge.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            isolated, project = root / "isolated", root / "project"
            source = ROOT / "skills" / "workflow-init"
            shutil.copytree(source / "scripts", isolated / "scripts")
            shutil.copytree(source / "templates", isolated / "templates")
            project.mkdir()
            result = subprocess.run(
                ["bash", str(isolated / "scripts" / "init.sh"),
                 "--dest", str(project), "--modules", "core,engineering"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("engineering-cycle", result.stderr)
            self.assertEqual(list(project.rglob("*")), [], "a failed run must leave the project untouched")

    def test_vendored_engineering_references_have_no_dangling_upstream_links(self):
        # The packs these were vendored from linked to a sibling ../../references/
        # directory their installer never fetched, so every such link was dead.
        # Vendoring is only worth doing if none of them survived the adaptation.
        references = ROOT / "skills" / "engineering-cycle" / "references"
        offenders = [
            str(path.relative_to(ROOT))
            for path in sorted(references.rglob("*.md"))
            if "../../references/" in path.read_text()
        ]
        self.assertEqual(offenders, [])

    def test_engineering_cycle_routes_only_to_files_that_exist(self):
        skill = ROOT / "skills" / "engineering-cycle" / "SKILL.md"
        targets = sorted(set(re.findall(r"`(references/[\w/.-]+\.md)`", skill.read_text())))
        self.assertTrue(targets, "engineering-cycle SKILL.md should route to its references")
        missing = [t for t in targets if not (skill.parent / t).is_file()]
        self.assertEqual(missing, [])

    def test_local_github_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issues = root / "issues.json"
            issues.write_text(json.dumps([{"title": "Build core flow", "body": "Acceptance criteria", "dependencies": ["GH-000"], "labels": ["mvp"]}]))
            output = root / "github"
            result = self.run_script("export_github_plan.py", str(issues), "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            exported = json.loads((output / "issue-plan.yaml").read_text())
            self.assertEqual(exported["publish_status"], "local_only")
            self.assertEqual(exported["issues"][0]["dependencies"], ["GH-000"])
            self.assertIn("Build core flow", (output / "issue-plan.md").read_text())

    def test_special_characters_are_safe_in_project_state(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_script("init_project.py", "A: #1 \"idea\"", "--directory", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            state = (Path(directory) / ".product-studio" / "project.yaml").read_text()
            self.assertIn('name: "A: #1 \\"idea\\""', state)

    def test_capabilities_can_be_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / ".product-studio" / "project.yaml"
            result = self.run_script("discover_capabilities.py", "--project", str(state))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("capability_registry_json", state.read_text())

    def test_original_lifecycle_scenarios_have_explicit_coverage(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        docs = "\n".join(path.read_text() for path in (ROOT / "docs/examples").glob("*.md"))
        required_terms = [
            "Prototype", "Hackathon", "Indie App", "SaaS", "Startup", "Production", "Custom",
            "Mobbin", "research plan", "GitHub Issues", "Resume", "Scope expansion",
            "MVP Auditor", "Product Synthesizer", "completion gate", "explicit confirmation",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, skill + docs)

    def test_fluid_workflow_rules_are_explicit(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        protocol = (ROOT / "skills/product-studio/references/qa-session.md").read_text()
        for phrase in [
            "phase checkpoints", "house rules", "done bar", "highest-impact gap",
            "independent review", "consequential", "protected outcome",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, (skill + protocol).lower())

    def test_specify_phase_is_documented_end_to_end(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        for phrase in ["Specify", "Behavior Spec", "BH-###", "AM-###", "ambiguity", "product-recheck", "docs/agent/BEHAVIORS.md"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)
        hardening = (ROOT / "skills/product-studio/references/spec-hardening.md").read_text().lower()
        for klass in ["term", "boundary", "actor", "state", "timing", "failure", "identity", "quantity", "visibility", "reversibility"]:
            with self.subTest(klass=klass):
                self.assertIn(f"`{klass}`", hardening)
        discovery = (ROOT / "skills/product-studio/references/behavior-discovery.md").read_text()
        self.assertIn("Product scope", discovery)
        self.assertIn("Behavior scope", discovery)
        self.assertIn("## Specification", (ROOT / "skills/product-studio/references/done-bars.md").read_text())

    def test_behavior_spec_format_marker_is_shared(self):
        marker = "<!-- behavior-spec/v1 -->"
        for name in ("templates/behavior-spec.md", "docs/examples/spec-hardening.md"):
            with self.subTest(name=name):
                self.assertIn(marker, (ROOT / name).read_text())

    def test_behavior_spec_validator_accepts_the_example_and_rejects_open_ambiguities(self):
        example = ROOT / "docs/examples/spec-hardening.md"
        result = self.run_script("validate_behavior_spec.py", str(example))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with tempfile.TemporaryDirectory() as directory:
            broken = Path(directory) / "behavior-spec.md"
            broken.write_text(example.read_text().replace("- Status: resolved -> D-007", "- Status: open"))
            result = self.run_script("validate_behavior_spec.py", str(broken))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("still open", result.stdout)
            result = self.run_script("validate_behavior_spec.py", str(broken), "--prototype")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = self.run_script("validate_behavior_spec.py", str(example), "--mirror", str(broken))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mirror out of sync", result.stdout)

    def test_implementation_brief_requires_behavior_citations(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            body = (
                "## Context\n- Behavior spec path: docs/agent/BEHAVIORS.md\n"
                "## Task\n- Objective: ship it\n"
                "## Constraints\n- House rules: protect the core flow\n- Non-negotiable acceptance criteria:\n  - the core flow completes\n"
                "## Verification — do not finish until\n- [x] tests pass — Evidence: tests/out.txt — Owner: implementation — Status: passed\n"
                "## Output Format\n- Files: src/core\n## Handoff\n- First action: run tests\n"
            )
            brief.write_text(body)
            result = self.run_script("validate_implementation_brief.py", str(brief))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cites no BH-###", result.stdout)
            brief.write_text(body.replace("- the core flow completes", "- BH-001 — the core flow completes"))
            result = self.run_script("validate_implementation_brief.py", str(brief))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_recheck_skill_is_public_and_reuses_shared_references(self):
        recheck = (ROOT / "skills/product-recheck/SKILL.md").read_text()
        self.assertTrue(recheck.startswith("---\nname: product-recheck\ndescription: "))
        for phrase in [
            "/product-recheck", "Continue", "Redirect", "Cut", "Stop",
            "Orphan test", "Coverage gap", "Stale test", "retired",
            "../product-studio/references/spec-hardening.md",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, recheck)

    def test_native_apple_track_prefers_xcodebuild_mcp_with_fallback(self):
        adapter = (ROOT / "skills/product-studio/adapters/xcodebuild-mcp/README.md").read_text().lower()
        for phrase in ["mcp__xcodebuildmcp__", "install", "xcodebuild", "fallback"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, adapter)
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        self.assertIn("XcodeBuildMCP", skill)
        self.assertIn("XcodeBuildMCP", (ROOT / "skills/product-studio/references/platform-decision.md").read_text())

    def test_workbench_is_optional_with_local_fallback(self):
        adapter = ROOT / "skills/product-studio/adapters/workbench/README.md"
        self.assertTrue(adapter.exists())
        text = adapter.read_text().lower()
        self.assertIn("optional", text)
        self.assertIn("local", text)

    def test_workflow_runner_requires_independent_review(self):
        state = new_state("demo")
        begin_phase(state, "product", ["wedge defined"])
        record_review(state, "product", "self", True, ["looks good"])
        checkpoint(state, "product")
        self.assertEqual(state["session"]["approval_status"], "self_review_only")
        self.assertEqual(state["phases"]["product"]["status"], "blocked")
        record_review(state, "product", "independent", True, [])
        checkpoint(state, "product")
        self.assertEqual(state["session"]["approval_status"], "approved")
        self.assertEqual(state["phases"]["product"]["status"], "checkpointed")

    def test_prototype_mode_rules_are_explicit(self):
        prototype = (ROOT / "skills/product-studio/references/prototype-mode.md").read_text()
        modes = (ROOT / "skills/product-studio/references/operating-modes.md").read_text()
        for phrase in ["mock boundary", "confirm", "expo", "validation question", "cut", "one runnable check"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prototype.lower())
        self.assertIn("Prototype", modes)

    def test_prototype_mode_clears_checkpoint_on_self_review(self):
        state = new_state("demo", mode="prototype")
        begin_phase(state, "mvp")
        record_review(state, "mvp", "self", True, [])
        checkpoint(state, "mvp")
        self.assertEqual(state["phases"]["mvp"]["status"], "checkpointed")
        self.assertEqual(state["session"]["approval_status"], "approved")

    def test_workflow_runner_repair_iteration_and_next_phase(self):
        state = new_state("demo")
        begin_phase(state, "product")
        record_review(state, "product", "independent", False, ["wedge too broad"])
        self.assertEqual(state["session"]["iteration_count"], 1)
        self.assertEqual(state["session"]["next_action"], "repair-highest-impact-gap")
        record_review(state, "product", "independent", True, [])
        checkpoint(state, "product")
        self.assertEqual(state["session"]["next_action"], "begin-research")

    def test_final_planning_checkpoint_blocks_unverified_or_missing_brief(self):
        state = new_state("demo")
        begin_phase(state, "final_planning")
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["final_planning"]["approval_status"], "blocked")
        self.assertFalse(can_handoff(state))
        attach_final_brief(state, "08-implementation-brief.md", ["07-production-blueprint.md"], [{"check": "tests pass", "evidence": "tests/output.txt", "owner": "implementation", "status": "unresolved"}])
        checkpoint(state, "final_planning")
        self.assertEqual(state["session"]["next_action"], "verification-checks-unresolved")
        self.assertFalse(can_handoff(state))

    def test_final_planning_checkpoint_allows_verified_independent_handoff(self):
        state = new_state("demo")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 0, True)
        begin_phase(state, "final_planning")
        attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"], [{"check": "tests pass", "evidence": "tests/output.txt", "owner": "implementation", "status": "passed"}])
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["final_planning"]["approval_status"], "approved")
        self.assertTrue(can_handoff(state))
        self.assertEqual(state["session"]["next_action"], "offer-completion-actions")

    def test_specify_checkpoint_blocks_until_ambiguities_are_closed(self):
        state = new_state("demo")
        begin_phase(state, "specify")
        record_review(state, "specify", "independent", True, [])
        checkpoint(state, "specify")
        self.assertEqual(state["session"]["next_action"], "behavior-spec-missing")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 7, 2, True)
        checkpoint(state, "specify")
        self.assertEqual(state["session"]["next_action"], "ambiguities-open")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 7, 0, False)
        checkpoint(state, "specify")
        self.assertEqual(state["session"]["next_action"], "behavior-spec-not-validated")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 7, 0, True)
        checkpoint(state, "specify")
        self.assertEqual(state["phases"]["specify"]["status"], "checkpointed")
        self.assertEqual(state["session"]["next_action"], "begin-mvp")

    def test_prototype_mode_warns_instead_of_blocking_on_open_ambiguities(self):
        state = new_state("demo", "prototype")
        begin_phase(state, "specify")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 4, 3, False)
        record_review(state, "specify", "self", True, [])
        checkpoint(state, "specify")
        self.assertEqual(state["phases"]["specify"]["status"], "checkpointed")
        self.assertIn("prototype-warning", state["phases"]["specify"]["result"])

    def test_unspecified_behaviors_block_the_implementation_brief(self):
        state = new_state("demo")
        begin_phase(state, "final_planning")
        attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"], [{"check": "tests pass", "evidence": "tests/output.txt", "owner": "implementation", "status": "passed"}])
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["session"]["next_action"], "behavior-spec-missing")
        self.assertFalse(can_handoff(state))

    def test_workbench_detection_and_local_fallback(self):
        self.assertEqual(detect()["status"], "unavailable")
        with tempfile.TemporaryDirectory() as directory:
            target = publish_local(Path(directory), {"phase": "product"})
            self.assertTrue(target.exists())
            self.assertIn("local_fallback", target.read_text())

    def test_final_planning_brief_requires_explicit_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = {
                "context": {"goal": "Ship the core flow", "audience": "indie users", "stage": "MVP", "source_artifacts": ["04-mvp-build-plan.md"], "context_sources": ["/repo/src", "/repo/tests"], "repository": "/repo", "behavior_spec": ".product-studio/artifacts/behavior-spec.md", "existing_tests": "/repo/tests", "design_references": "unavailable", "documentation": "/repo/docs", "previous_versions": "unavailable", "prior_review_findings": "unavailable"},
                "task": {"objective": "Implement the first vertical slice", "user_outcome": "Users complete the core flow", "in_scope": ["core flow", "error state"], "first_vertical_slice": "Create and complete an item"},
                "constraints": {"house_rules": ["protect the core flow"], "scope_exclusions": ["billing"], "acceptance_criteria": ["BH-001 — core flow completes"], "technical": ["native iOS"]},
                "verification": {"do_not_finish_until": [{"check": "Core flow test passes", "evidence": "tests/core", "status": "unresolved", "owner": "implementation"}], "evidence": [], "unresolved": ["real API quota"]},
                "output_format": {"files": ["src/core"], "completion_evidence": ["test output"]},
                "handoff": {"first_action": "Run the core test", "dependencies": ["repository"], "next_checkpoint": "after core flow"},
            }
            input_path = root / "brief.json"
            output_path = root / "08-implementation-brief.md"
            input_path.write_text(json.dumps(payload))
            result = self.run_script("build_implementation_brief.py", str(input_path), "--output", str(output_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.run_script("validate_implementation_brief.py", str(output_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("do not finish until", output_path.read_text())

    def test_final_planning_brief_without_verification_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "brief.md"
            brief.write_text("## Context\n## Task\n## Constraints\n## Verification — do not finish until\n## Output Format\n## Handoff\n")
            result = self.run_script("validate_implementation_brief.py", str(brief))
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
