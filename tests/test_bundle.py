from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
sys.path.insert(0, str(ROOT / "scripts"))
from workflow_runner import attach_final_brief, begin_phase, can_handoff, checkpoint, new_state, record_review  # noqa: E402
from workbench_adapter import detect, publish_local  # noqa: E402


class BundleTests(unittest.TestCase):
    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([PYTHON, str(ROOT / "scripts" / name), *args], cwd=ROOT, text=True, capture_output=True)

    def test_bundle_validates(self):
        result = self.run_script("validate_bundle.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_skill_starts_with_qa_and_mode_routing(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        for phrase in ["What do you want to build or improve?", "Hackathon", "Indie App", "SaaS", "Startup", "wait for explicit confirmation", "Expo", "Flutter", "SwiftUI", "Next.js", "market probe", "Mode revisit"]:
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
            result = self.run_script("install.py", "--target", "agents", "--destination", str(destination), "--uninstall")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((destination / "product-studio").exists())

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
            "Hackathon", "Indie App", "SaaS", "Startup", "Production", "Custom",
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
        begin_phase(state, "final_planning")
        attach_final_brief(state, "08-implementation-brief.md", ["04-mvp-build-plan.md"], [{"check": "tests pass", "evidence": "tests/output.txt", "owner": "implementation", "status": "passed"}])
        record_review(state, "final_planning", "independent", True, [])
        checkpoint(state, "final_planning")
        self.assertEqual(state["final_planning"]["approval_status"], "approved")
        self.assertTrue(can_handoff(state))
        self.assertEqual(state["session"]["next_action"], "offer-completion-actions")

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
                "context": {"goal": "Ship the core flow", "audience": "indie users", "stage": "MVP", "source_artifacts": ["04-mvp-build-plan.md"], "context_sources": ["/repo/src", "/repo/tests"], "repository": "/repo", "existing_tests": "/repo/tests", "design_references": "unavailable", "documentation": "/repo/docs", "previous_versions": "unavailable", "prior_review_findings": "unavailable"},
                "task": {"objective": "Implement the first vertical slice", "user_outcome": "Users complete the core flow", "in_scope": ["core flow", "error state"], "first_vertical_slice": "Create and complete an item"},
                "constraints": {"house_rules": ["protect the core flow"], "scope_exclusions": ["billing"], "acceptance_criteria": ["core flow completes"], "technical": ["native iOS"]},
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
