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
from workflow_runner import attach_behavior_spec, attach_final_brief, begin_phase, can_finish, can_handoff, checkpoint, deploy, mark_implementation_done, new_state, record_answer, record_review, save  # noqa: E402
import workflow_profile  # noqa: E402
from validate_behavior_spec import validate as validate_spec  # noqa: E402
from validate_implementation_brief import validate as validate_brief  # noqa: E402
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
            path = Path(directory) / ".product-studio" / "project.json"
            self.assertTrue(path.exists())
            state = json.loads(path.read_text())
            self.assertEqual(state["project"]["mode"], "hackathon")
            self.assertEqual(state["project"]["name"], "Test App")
            self.assertEqual(state["workflow_profile"], workflow_profile.compile_profile("hackathon"))
            self.assertEqual(state["session"]["current_phase"], "intake")
            self.assertEqual(state["session"]["approval_status"], "pending")
            self.assertIsNone(state["session"]["last_checkpoint"])
            self.assertIn("house_rules", state)
            self.assertIn("final_planning", state)
            self.assertTrue(state["phases"]["specify"]["done_bar"])
            self.assertTrue((path.parent / "artifacts").is_dir())

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
            state = json.loads((Path(directory) / ".product-studio" / "project.json").read_text())
            self.assertEqual(state["project"]["name"], 'A: #1 "idea"')

    def test_capabilities_persist_without_clobbering_state(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_script("init_project.py", "Test App", "--directory", directory, "--mode", "saas")
            path = Path(directory) / ".product-studio" / "project.json"
            result = self.run_script("discover_capabilities.py", "--project", str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
            state = json.loads(path.read_text())
            self.assertIn("integrations", state["capabilities"])
            self.assertEqual(state["workflow_profile"]["mode"], "saas")

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

    def test_idea_validation_runs_before_intent_extraction_for_rough_ideas(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        start = skill.index("## Start every session")
        end = skill.index("## Goal and house rules")
        start_every_session = skill[start:end]
        idea_validation_pos = start_every_session.index("references/idea-validation.md")
        hypothesis_pos = start_every_session.index("state a one-sentence hypothesis")
        self.assertLess(idea_validation_pos, hypothesis_pos)
        routing = skill[skill.index("## Stage routing"):skill.index("## Specification")]
        for row in ["Rough idea", "Prototype / idea validation"]:
            with self.subTest(row=row):
                line = next(l for l in routing.splitlines() if l.startswith(f"| {row} "))
                self.assertIn("Idea Validation", line)
        for row in ["Existing research", "Existing UX/UI", "MVP planning/build",
                    "Mid-development re-evaluation", "Existing MVP", "Production need",
                    "GitHub delivery", "Resume"]:
            with self.subTest(row=row):
                line = next(l for l in routing.splitlines() if l.startswith(f"| {row} "))
                self.assertNotIn("Idea Validation", line)

    def test_idea_validation_requires_explicit_confirmation_to_continue(self):
        protocol = (ROOT / "skills/product-studio/references/idea-validation.md").read_text()
        for phrase in ["explicit choice", "whatever you think", "sounds good", "silence",
                       "deferrals, not agreement", "Continue", "Refine"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, protocol)

    def test_idea_validation_refine_loop_reruns_bounded_research(self):
        protocol = " ".join((ROOT / "skills/product-studio/references/idea-validation.md").read_text().split())
        for phrase in ["Refine loop", "GUESS:", "re-run the bounded research pass",
                       "re-present the checkpoint", "No fixed round cap", "running round count"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, protocol)

    def test_idea_validator_capability_and_index_are_registered(self):
        index = (ROOT / "skills/product-studio/references/capabilities/index.md").read_text()
        self.assertIn("idea-validator.md", index)
        contract = (ROOT / "skills/product-studio/references/capabilities/idea-validator.md").read_text()
        for phrase in ["Purpose", "Inputs", "Outputs", "Gate", "Handoff"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)

    def test_prototype_research_rule_defers_to_idea_validation(self):
        prototype = (ROOT / "skills/product-studio/references/prototype-mode.md").read_text()
        self.assertIn("Already satisfied by `references/idea-validation.md`", prototype)

    def test_product_opportunity_template_has_validation_section(self):
        template = (ROOT / "templates/product-opportunity.md").read_text()
        self.assertIn("## Validation", template)
        self.assertLess(template.index("## Validation"), template.index("## Summary"))

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

    def test_hackathon_mode_rules_are_explicit(self):
        hackathon = (ROOT / "skills/product-studio/references/hackathon-mode.md").read_text().lower()
        for phrase in ["hero moment", "demo script", "fallback", "mock", "cut", "high-signal"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, hackathon)
        # The refinement that distinguishes it from Prototype's "one runnable check".
        self.assertIn("integration smoke test", hackathon)
        self.assertIn("Hackathon", (ROOT / "skills/product-studio/references/done-bars.md").read_text())

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

    def test_final_planning_checkpoint_blocks_a_missing_or_malformed_brief(self):
        state = new_state("demo")
        begin_phase(state, "final_planning")
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["final_planning"]["approval_status"], "blocked")
        self.assertFalse(can_handoff(state))
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 0, True)
        for check, reason in (
            ({"check": "tests pass", "evidence": "tests/output.txt", "status": "unresolved"}, "verification-owner-missing"),
            ({"check": "tests pass", "evidence": "tests/output.txt", "owner": "implementation", "status": "probably"}, "verification-status-invalid"),
            ({"check": "", "evidence": "tests/output.txt", "owner": "implementation", "status": "unresolved"}, "verification-check-description-missing"),
        ):
            with self.subTest(reason=reason):
                attach_final_brief(state, "08-implementation-brief.md", ["07-production-blueprint.md"], [check])
                checkpoint(state, "final_planning")
                self.assertEqual(state["session"]["next_action"], reason)
                self.assertFalse(can_handoff(state))

    def test_brief_with_pending_implementation_checks_hands_off_but_cannot_finish(self):
        # The stopping conditions in a brief are future conditions by construction.
        # Requiring them satisfied before handoff would only let finished work hand off.
        state = new_state("demo")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 0, True)
        begin_phase(state, "final_planning")
        attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"], [{"check": "the core-flow test passes", "evidence": "tests/core/", "owner": "implementation", "status": "unresolved"}])
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["final_planning"]["approval_status"], "approved")
        self.assertTrue(can_handoff(state))
        self.assertFalse(can_finish(state))
        mark_implementation_done(state)
        self.assertEqual(state["session"]["next_action"], "verification-checks-unresolved")
        self.assertFalse(can_finish(state))
        state["final_planning"]["verification"]["do_not_finish_until"][0]["status"] = "passed"
        mark_implementation_done(state)
        self.assertTrue(can_finish(state))
        self.assertEqual(state["final_planning"]["verification"]["unresolved"], [])

    def test_user_owned_checks_block_handoff(self):
        # A decision only the user can make is a missing input, not a future condition.
        state = new_state("demo")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 0, True)
        begin_phase(state, "final_planning")
        attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"], [{"check": "user picks the pricing tier", "evidence": "session decision D-004", "owner": "user", "status": "unresolved"}])
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["session"]["next_action"], "user-decisions-unresolved")
        self.assertFalse(can_handoff(state))

    def test_evidence_placeholder_is_rejected_in_any_wording(self):
        for evidence, blocks in (("To be supplied", True), ("TBD", True), ("", True), ("  n/a ", True), ("none.", True), ("tests/output.txt", False)):
            with self.subTest(evidence=evidence):
                state = new_state("demo")
                attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 0, True)
                begin_phase(state, "final_planning")
                attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"], [{"check": "tests pass", "evidence": evidence, "owner": "implementation", "status": "unresolved"}])
                record_review(state, "final_planning", "independent", True, [])
                checkpoint(state, "final_planning")
                self.assertEqual(state["session"]["next_action"] == "verification-evidence-source-missing", blocks)
                self.assertEqual(can_handoff(state), not blocks)

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
        mark_implementation_done(state)
        self.assertTrue(can_finish(state))

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


class ProfileScenarioTests(unittest.TestCase):
    """Scenarios, not phrases. Each drives the runner and asserts the gates a mode claims."""

    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([PYTHON, str(ROOT / "scripts" / name), *args], cwd=ROOT, text=True, capture_output=True)

    def _brief(self, state, checks=None):
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 0, True)
        begin_phase(state, "final_planning")
        attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"],
                           checks or [{"check": "the hero-moment test passes", "evidence": "tests/core/", "owner": "implementation", "status": "unresolved"}])
        return state

    def test_four_hour_hackathon_reaches_implementation_on_a_self_review(self):
        state = new_state("citytravel", "hackathon")
        # A spec left deliberately unclosed inside the timebox warns; it does not block.
        begin_phase(state, "specify")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 6, 2, False)
        record_review(state, "specify", "self", True, [])
        checkpoint(state, "specify")
        self.assertEqual(state["phases"]["specify"]["status"], "checkpointed")
        self.assertIn("hackathon-warning", state["phases"]["specify"]["result"])
        # One high-signal check, still pending, still hands off.
        self._brief(state)
        record_review(state, "final_planning", "self", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["final_planning"]["approval_status"], "approved")
        self.assertTrue(can_handoff(state))
        self.assertFalse(can_finish(state))

    def test_prototype_exit_and_revisit_behavior_is_unchanged(self):
        profile = workflow_profile.compile_profile("prototype")
        self.assertEqual(profile["planning"]["spec_gate"], "warn")
        self.assertFalse(profile["review"]["independent_required"])
        self.assertEqual(profile["revisit_when"], "the validation question is answered")
        state = new_state("demo", "prototype")
        begin_phase(state, "specify")
        attach_behavior_spec(state, "behavior-spec.md", "docs/agent/BEHAVIORS.md", 4, 3, False)
        record_review(state, "specify", "self", True, [])
        checkpoint(state, "specify")
        self.assertIn("prototype-warning", state["phases"]["specify"]["result"])

    def test_durable_modes_require_gates_and_never_auto_deploy(self):
        for mode in ("indie", "saas", "startup"):
            with self.subTest(mode=mode):
                profile = workflow_profile.compile_profile(mode)
                self.assertTrue(profile["review"]["independent_required"])
                self.assertTrue(profile["testing"]["ci_required"])
                self.assertEqual(profile["planning"]["spec_gate"], "block")
                self.assertFalse(profile["deployment"]["allowed"])
                # A self review is honestly reported, never silently promoted.
                state = new_state("app", mode)
                begin_phase(state, "mvp")
                record_review(state, "mvp", "self", True, [])
                checkpoint(state, "mvp")
                self.assertEqual(state["session"]["approval_status"], "self_review_only")
                self.assertNotEqual(state["phases"]["mvp"]["status"], "checkpointed")

    def test_production_requires_security_observability_rollout_rollback_and_approval(self):
        profile = workflow_profile.compile_profile("production")
        for control in ("security-review", "observability", "rollout-plan", "rollback-plan", "human-approval-gate"):
            self.assertIn(control, profile["safety_floor"])
        self.assertEqual(profile["design"]["gate"], "evidence_required")
        self.assertFalse(profile["deployment"]["allowed"])
        # A complete design artifact is not enough at this risk tier.
        state = new_state("platform", "production")
        begin_phase(state, "design")
        record_review(state, "design", "independent", True, [])
        checkpoint(state, "design")
        self.assertEqual(state["session"]["next_action"], "design-evidence-missing")
        state["design"]["evidence"] = ["clickable prototype, 3 participants"]
        checkpoint(state, "design")
        self.assertEqual(state["phases"]["design"]["status"], "checkpointed")

    def test_deployment_is_an_explicit_transition_with_preconditions(self):
        state = new_state("platform", "production")
        deploy(state, "production", environment="prod-us", approver="quan", rollback="revert tag", observability="error rate", thresholds="see ship.md")
        self.assertEqual(state["session"]["next_action"], "deployment-not-enabled-in-profile")
        state["workflow_profile"] = workflow_profile.compile_profile("production", {"deployment": {"allowed": True}})
        deploy(state, "production", environment="prod-us", approver="quan")
        self.assertIn("deployment-preconditions-missing", state["session"]["next_action"])
        deploy(state, "production", environment="prod-us", approver="quan", rollback="revert tag", observability="error rate + p95", thresholds="advance <10% delta")
        self.assertEqual(state["session"]["next_action"], "verify-in-production")
        self.assertEqual(state["production"]["deployment"]["approver"], "quan")

    def test_deployment_cannot_be_opted_into_below_staging(self):
        with self.assertRaises(ValueError):
            workflow_profile.compile_profile("indie", {"deployment": {"allowed": True}})

    def test_safety_floor_cannot_be_overridden_away(self):
        profile = workflow_profile.compile_profile("saas", {"safety_floor": []})
        self.assertIn("secrets-out-of-repo", profile["safety_floor"])
        self.assertIn("authz-per-tenant", profile["safety_floor"])

    def test_high_risk_override_derives_the_design_evidence_gate(self):
        profile = workflow_profile.compile_profile("indie", {"risk_tier": "high"})
        self.assertEqual(profile["design"]["gate"], "evidence_required")
        self.assertIn("human-approval-gate", profile["safety_floor"])

    def test_merge_policy_and_review_lane_compile_for_every_mode(self):
        for mode in workflow_profile.MODE_PROFILES:
            with self.subTest(mode=mode):
                profile = workflow_profile.compile_profile(mode)
                # A lane only exists where an independent review does, and where one does it is
                # never `none` — that pairing would compile a required review nobody runs.
                if profile["review"]["independent_required"]:
                    self.assertIn(profile["review"]["lane"], ("offline", "online"))
                else:
                    self.assertEqual(profile["review"]["lane"], "none")
                self.assertIn(profile["development"]["merge_policy"], workflow_profile.MERGE_POLICIES)
        # `ask` everywhere except the risk tier that names a human approval gate.
        self.assertEqual(workflow_profile.compile_profile("indie")["development"]["merge_policy"], "ask")
        self.assertEqual(workflow_profile.compile_profile("production")["development"]["merge_policy"], "never")

    def test_high_risk_refuses_to_let_the_agent_merge_its_own_pr(self):
        for overrides in ({"development": {"merge_policy": "auto_on_approve"}}, {"development": {"merge_policy": "ask"}}):
            with self.subTest(overrides=overrides):
                self.assertEqual(workflow_profile.compile_profile("production", overrides)["development"]["merge_policy"], "never")
        # And the derivation follows the tier, not the mode label.
        self.assertEqual(
            workflow_profile.compile_profile("indie", {"risk_tier": "high", "development": {"merge_policy": "auto_on_approve"}})["development"]["merge_policy"],
            "never",
        )

    def test_invalid_merge_policy_or_orphaned_review_requirement_is_refused(self):
        with self.assertRaises(ValueError):
            workflow_profile.compile_profile("indie", {"development": {"merge_policy": "yolo"}})
        with self.assertRaises(ValueError):
            workflow_profile.compile_profile("indie", {"review": {"lane": "postal"}})
        with self.assertRaises(ValueError):
            workflow_profile.compile_profile("indie", {"review": {"lane": "none"}})

    def test_generated_merge_gate_has_a_mechanism_behind_it(self):
        init = ROOT / "skills/workflow-init"
        settings = json.loads((init / "templates/claude-code/settings.json").read_text())
        # `ask` works precisely because the permission prompt fires; an allow entry silences it.
        self.assertNotIn("Bash(gh pr merge:*)", settings["permissions"]["allow"])
        hook = (init / "templates/claude-code/hooks/require-verdict.sh").read_text()
        self.assertIn('MERGE_POLICY="{{MERGE_POLICY}}"', hook)
        for policy in workflow_profile.MERGE_POLICIES:
            self.assertIn(policy, hook)
        self.assertIn(".review", hook)
        self.assertIn("--admin", hook)
        skill = (init / "SKILL.md").read_text()
        for placeholder in ("{{MERGE_POLICY}}", "{{MERGE_POLICY_TEXT}}", "{{MERGE_POLICY_LINE}}"):
            self.assertIn(placeholder, skill)
        self.assertIn("{{MERGE_POLICY_TEXT}}", (init / "templates/core/AGENTS.md").read_text())
        self.assertIn("{{MERGE_POLICY_LINE}}", (init / "templates/core/docs/agent/CARD.md").read_text())
        self.assertIn("{{MERGE_POLICY}}", (init / "templates/core/docs/agent/RUNBOOKS.md").read_text())

    def test_merge_gate_survives_the_obvious_ways_around_it(self):
        """A gate a leading `PAGER=cat` walks past is not a gate."""
        hook = (ROOT / "skills/workflow-init/templates/claude-code/hooks/require-verdict.sh").read_text()
        filled = (hook
                  .replace("{{SOURCE_DIRS_RE}}", "src").replace("{{TEST_DIRS}}", "")
                  .replace("{{PROJECT_SLUG}}", "gate-test").replace("{{DEFAULT_BRANCH}}", "main")
                  .replace("{{MERGE_POLICY}}", "never"))
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "require-verdict.sh"
            script.write_text(filled)
            blocked = ("gh pr merge 1", "PAGER=cat gh pr merge 1", "env gh pr merge 1",
                       "command gh pr merge 1", "sudo gh pr merge 1", "A=1 B=2 gh pr merge 1",
                       "true && PAGER=cat gh pr merge 1", "ls | gh pr merge 1", "echo hi & gh pr merge 1",
                       "(gh pr merge 1)", "x=1\ngh pr merge 1",
                       # Blanking quotes must not let a real merge hide behind one.
                       'gh pr merge 1 --subject "fix: it"', 'echo "a; b" ; gh pr merge 1',
                       'echo "unclosed ; gh pr merge 1', 'echo "a ; gh pr merge 1" ; gh pr merge 2',
                       # Two apostrophes inside double-quoted arguments straddling the merge.
                       # A single-quote substitution pass blanked everything between them and the
                       # gate went silent — a fail-open on the commonest shape an agent writes.
                       'echo "it\'s done" && gh pr merge 1 && echo "that\'s all"',
                       'git commit -m "it\'s ready" && gh pr merge 1 --squash && echo "that\'s all"',
                       'gh pr comment 1 --body "reviewer\'s happy" && gh pr merge 1',
                       'gh pr merge "1"', "gh pr merge --squash 7",
                       "(gh pr merge 7)", "true&&gh pr merge 7",
                       'gh pr comment 7 --body "run gh pr merge 3" && gh pr merge 7')
            # Quoted text is blanked before matching, so the orchestrator can still post the
            # review and open a PR whose body describes the merge flow.
            allowed = ("ls -la", "git commit -m 'note about gh pr merge later'", "echo gh pr create",
                       "gh pr list | grep 'gh pr merge'",
                       'gh pr comment 1 --body "do not (gh pr merge) yet"',
                       'gh pr comment 1 --body "next step; gh pr merge"')
            for command in blocked + allowed:
                payload = json.dumps({"tool_input": {"command": command}})
                result = subprocess.run(["bash", str(script)], input=payload, cwd=directory, text=True, capture_output=True)
                with self.subTest(command=command):
                    self.assertEqual('"decision":"block"' in result.stdout, command in blocked, result.stdout)
                    if result.stdout.strip():
                        # A hook whose stdout does not parse is not a block. This is the
                        # inversion that let a REQUEST-CHANGES marker permit a merge.
                        json.loads(result.stdout)

    def test_block_reason_escapes_content_read_from_a_verdict_file(self):
        """The reviewer writes verdict lines as prose; the earlier test drove block() through a
        placeholder, which left the path that actually reads a file uncovered."""
        hook = (ROOT / "skills/workflow-init/templates/claude-code/hooks/require-verdict.sh").read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            verdicts = root / "verdicts"
            verdicts.mkdir()
            filled = (hook
                      .replace("{{SOURCE_DIRS_RE}}", "src").replace("{{TEST_DIRS}}", "")
                      .replace("{{DEFAULT_BRANCH}}", "main").replace("{{MERGE_POLICY}}", "never")
                      .replace('VERDICT_DIR="/tmp/{{PROJECT_SLUG}}-verdicts"', f'VERDICT_DIR="{verdicts}"'))
            script = root / "require-verdict.sh"
            script.write_text(filled)
            for command in ("git", "init", "-q"), ("git", "config", "user.email", "t@t"), ("git", "config", "user.name", "t"):
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            source = root / "src"
            source.mkdir()
            # Two commits: the heavy lane triggers off a diff, and HEAD~1 has to exist.
            for index, body in enumerate(("x = 1\n", "x = 2\n")):
                (source / "app.py").write_text(body)
                subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-qm", f"c{index}"], cwd=root, check=True, capture_output=True)
            sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True).stdout.strip()
            (verdicts / sha).write_text('FIX-FIRST: broke the "auth" path and a \\ backslash\nevidence\n')
            payload = json.dumps({"tool_input": {"command": "gh pr create --fill"}})
            result = subprocess.run(["bash", str(script)], input=payload, cwd=root, text=True, capture_output=True)
            decision = json.loads(result.stdout)   # fails loudly if the reason was spliced raw
            self.assertEqual(decision["decision"], "block")
            self.assertIn("auth", decision["reason"])

    def test_block_reason_stays_parseable_json_with_hostile_marker_text(self):
        """The reviewer writes the marker's first line as prose; a bare quote must not void the block."""
        hook = (ROOT / "skills/workflow-init/templates/claude-code/hooks/require-verdict.sh").read_text()
        filled = (hook
                  .replace("{{SOURCE_DIRS_RE}}", "src").replace("{{TEST_DIRS}}", "")
                  .replace("{{PROJECT_SLUG}}", "gate-json").replace("{{DEFAULT_BRANCH}}", "main")
                  .replace("{{MERGE_POLICY}}", 'REQUEST-CHANGES: unescaped "quote" and \\ backslash'))
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "require-verdict.sh"
            script.write_text(filled)
            payload = json.dumps({"tool_input": {"command": "gh pr merge 1"}})
            result = subprocess.run(["bash", str(script)], input=payload, cwd=directory, text=True, capture_output=True)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["decision"], "block")
            self.assertIn("quote", decision["reason"])

    def test_merge_gate_identifies_which_pr_is_being_merged(self):
        """`gh pr merge 7` merges PR 7 whatever is checked out, so the ref decides which marker
        counts. Every outcome that is not an unambiguous ref, or a genuinely bare merge, must
        block — "parser found nothing" silently meaning "the current branch" is the fail-open
        this guards, and it was reachable twice."""
        hook = (ROOT / "skills/workflow-init/templates/claude-code/hooks/require-verdict.sh").read_text()
        program = hook.split("| awk '", 1)[1].split("')\n", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            parser = Path(directory) / "ref.awk"
            parser.write_text(program)
            cases = {
                "gh pr merge 7": (0, "7"),
                "gh pr merge --squash 7": (0, "7"),
                "gh pr merge --auto --squash 7": (0, "7"),
                "gh pr merge 7 && echo done": (0, "7"),
                # Operators glued to `gh` used to yield "no merge found" -> the current branch.
                "(gh pr merge 7)": (0, "7"),
                "true&&gh pr merge 7": (0, "7"),
                # A genuinely bare merge is the one case that legitimately means "this branch".
                "gh pr merge --squash --delete-branch": (0, ""),
                "gh pr merge": (0, ""),
                "gh pr merge 7 8": (3, ""),      # ambiguous
                'gh pr merge ""': (4, ""),       # quoted or from a variable: unresolvable
            }
            for command, (status, ref) in cases.items():
                padded = subprocess.run(["sed", "s/[()&|;]/ & /g"], input=command, text=True, capture_output=True).stdout
                result = subprocess.run(["awk", "-f", str(parser)], input=padded, text=True, capture_output=True)
                with self.subTest(command=command):
                    self.assertEqual(result.returncode, status, result.stderr)
                    self.assertEqual(result.stdout.strip(), ref)

    def test_merge_gate_and_its_ref_parser_read_the_same_command(self):
        """The gate fired on the real merge while the parser locked onto a `gh pr merge` inside
        a --body, so they disagreed about which PR was being merged."""
        hook = (ROOT / "skills/workflow-init/templates/claude-code/hooks/require-verdict.sh").read_text()
        self.assertIn('''pr_ref=$(printf '%s' "$unquoted"''', hook)
        self.assertNotIn('''pr_ref=$(printf '%s' "$command"''', hook)
        # Every non-zero parser status has a block arm; a missing one falls through to the
        # bare-merge path, which resolves the current branch's PR.
        arms = hook.split("case $? in", 1)[1].split("esac", 1)[0]
        for status in ("2)", "3)", "4)"):
            self.assertIn(status, arms)
            self.assertIn("block", arms)

    def test_worked_profile_example_matches_what_the_compiler_emits(self):
        """A reader copies this JSON into their state file; drift ships them a profile the
        gates are told to read fields from that are not there."""
        text = (ROOT / "docs/examples/hackathon-ios.md").read_text()
        blob = re.search(r'\{\s*"version": "workflow_profile/v1".*?\n\}', text, re.S)
        self.assertIsNotNone(blob, "the hackathon example no longer contains a compiled profile")
        self.assertEqual(json.loads(blob.group(0)), workflow_profile.compile_profile("hackathon"))

    def test_gate_three_has_the_qa_agent_it_tells_you_to_spawn(self):
        init = ROOT / "skills/workflow-init"
        qa = (init / "templates/agents/qa-agent.md").read_text()
        for placeholder in ("{{QA_SURFACE}}", "{{QA_TOOLS}}", "{{QA_RUN_CMD}}", "{{QA_TOOLING}}"):
            self.assertIn(placeholder, qa)
        # The tools line is a placeholder because a fixed one would forbid the MCP tools the
        # body tells the agent to use — an unusable agent that still looks correctly written.
        self.assertIn("tools: {{QA_TOOLS}}", qa)
        for placeholder in ("{{QA_SURFACE}}", "{{QA_TOOLS}}", "{{QA_RUN_CMD}}", "{{QA_TOOLING}}"):
            self.assertIn(placeholder, (init / "SKILL.md").read_text())
        # QA reports evidence; it never writes the marker that unblocks a merge.
        self.assertIn("Never write a verdict marker", qa)
        self.assertIn("agents/qa-agent.md|.claude/agents/_qa-agent.template.md", (init / "scripts/init.sh").read_text())
        self.assertIn("_qa-agent.template.md", (init / "SKILL.md").read_text())

    def test_unknown_mode_is_refused_at_every_entry_point(self):
        with self.assertRaises(ValueError):
            workflow_profile.compile_profile("hakathon")
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_script("init_project.py", "Typo", "--directory", directory, "--mode", "hakathon")
            self.assertNotEqual(result.returncode, 0)

    def test_mode_enum_matches_the_schema_and_the_skill(self):
        schema = json.loads((ROOT / "schemas/project.schema.json").read_text())
        self.assertEqual(sorted(workflow_profile.MODE_PROFILES), sorted(schema["properties"]["project"]["properties"]["mode"]["enum"]))
        profile_schema = json.loads((ROOT / "schemas/workflow-profile.schema.json").read_text())
        self.assertEqual(sorted(workflow_profile.MODE_PROFILES), sorted(profile_schema["properties"]["mode"]["enum"]))
        self.assertEqual(profile_schema["properties"]["version"]["const"], workflow_profile.VERSION)
        # Every compiled value is a member of the enum the schema publishes.
        for mode in workflow_profile.MODE_PROFILES:
            compiled = workflow_profile.compile_profile(mode)
            with self.subTest(mode=mode):
                self.assertIn(compiled["risk_tier"], profile_schema["properties"]["risk_tier"]["enum"])
                self.assertIn(compiled["delivery_target"], profile_schema["properties"]["delivery_target"]["enum"])
                self.assertIn(compiled["design"]["gate"], profile_schema["properties"]["design"]["properties"]["gate"]["enum"])
                self.assertIn(compiled["development"]["merge_policy"], profile_schema["properties"]["development"]["properties"]["merge_policy"]["enum"])
                self.assertIn(compiled["review"]["lane"], profile_schema["properties"]["review"]["properties"]["lane"]["enum"])
        table = (ROOT / "skills/product-studio/references/workflow-profile.md").read_text()
        for mode in workflow_profile.MODE_PROFILES:
            self.assertIn(mode, table)

    def test_behavior_cap_is_enforced_per_mode(self):
        # The mode references state a behavior range in prose; this is the mechanism.
        spec = (ROOT / "docs/examples/spec-hardening.md").read_text()
        body = spec.split("## BH-014 — Cancel succeeds before packing\n", 1)[1].split("\n\n", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            seven = Path(directory) / "seven.md"
            seven.write_text(spec)
            self.assertEqual([e for e in validate_spec(seven, mode="prototype") if "cap" in e], [])
            eight = Path(directory) / "eight.md"
            eight.write_text(spec.replace("\n## Ambiguity register", "\n## BH-901 — one behavior too many\n" + body + "\n\n## Ambiguity register", 1))
            self.assertTrue([e for e in validate_spec(eight, mode="prototype") if "cap" in e])
            self.assertEqual([e for e in validate_spec(eight, mode="hackathon") if "cap" in e], [])
            self.assertEqual([e for e in validate_spec(eight, mode="saas") if "cap" in e], [])

    def test_generated_ci_follows_the_profile_and_degrades_without_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            emitted = {}
            for name, mode in (("fast", "hackathon"), ("durable", "saas")):
                dest = root / name
                dest.mkdir()
                self.run_script("init_project.py", name, "--directory", str(dest), "--mode", mode)
                subprocess.run(["bash", str(ROOT / "skills/workflow-init/scripts/init.sh"), "--dest", str(dest), "--modules", "ci"], check=True, capture_output=True)
                emitted[name] = (dest / ".github/workflows/ci.yml").read_text()
            # no product-studio state at all: workflow-init must still work, and match the stub
            bare = root / "bare"
            bare.mkdir()
            subprocess.run(["bash", str(ROOT / "skills/workflow-init/scripts/init.sh"), "--dest", str(bare), "--modules", "ci"], check=True, capture_output=True)
            emitted["bare"] = (bare / ".github/workflows/ci.yml").read_text()

        self.assertEqual(emitted["fast"], emitted["bare"])
        self.assertNotEqual(emitted["fast"], emitted["durable"])
        self.assertNotIn("\n  push:", emitted["fast"])
        # ci.md's verify bar: the pipeline runs on PRs and on default-branch pushes
        self.assertIn("\n  push:", emitted["durable"])
        for gate in ("lint:", "typecheck:", "test:", "build:", "integration:", "audit:"):
            with self.subTest(gate=gate):
                self.assertIn(gate, emitted["durable"])

    def test_canonical_state_survives_init_answers_mode_checkpoint_and_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_script("init_project.py", "Resume Me", "--directory", directory, "--mode", "indie")
            path = Path(directory) / ".product-studio" / "project.json"
            state = json.loads(path.read_text())
            record_answer(state, "who is this for?", "solo founders", decision_id="D-001")
            begin_phase(state, "product")
            record_review(state, "product", "independent", True, [])
            checkpoint(state, "product")
            save(path, state)

            resumed = json.loads(path.read_text())
            self.assertEqual(resumed["project"]["mode"], "indie")
            self.assertEqual(resumed["workflow_profile"], workflow_profile.compile_profile("indie"))
            self.assertEqual(resumed["session"]["questions"][0]["decision_id"], "D-001")
            self.assertEqual(resumed["session"]["last_checkpoint"]["phase"], "product")
            self.assertEqual(resumed["session"]["next_action"], "begin-research")
            # and the runner can still act on the file it just wrote
            checkpoint(resumed, "product")
            self.assertEqual(resumed["phases"]["product"]["status"], "checkpointed")

    def test_brief_validator_rejects_a_deployment_the_profile_forbids(self):
        brief = (ROOT / "templates/implementation-brief.md").read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brief.md"
            path.write_text(brief.replace("- Next checkpoint:", "- Next checkpoint: deploy to production"))
            errors = validate_brief(path, mode="saas")
            self.assertTrue([e for e in errors if "does not allow" in e])

    def test_brief_validator_requires_an_owner_on_every_check(self):
        brief = (ROOT / "templates/implementation-brief.md").read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brief.md"
            path.write_text(brief.replace(" — Owner: — Status: unresolved", " — Status: unresolved"))
            self.assertIn("every verification item must name an owner", validate_brief(path))

    def test_every_public_skill_ships_interface_metadata(self):
        for name in ("product-studio", "workflow-init", "engineering-cycle", "product-recheck"):
            with self.subTest(skill=name):
                meta = (ROOT / "skills" / name / "agents/openai.yaml").read_text()
                self.assertIn("display_name:", meta)
                self.assertIn("short_description:", meta)
                self.assertIn(name, (ROOT / "skills" / name / "SKILL.md").read_text())
                self.assertIn(name.split("-")[0], meta.lower())

