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
from workflow_runner import begin_phase, checkpoint, new_state, record_review  # noqa: E402
from workbench_adapter import detect, publish_local  # noqa: E402


class BundleTests(unittest.TestCase):
    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([PYTHON, str(ROOT / "scripts" / name), *args], cwd=ROOT, text=True, capture_output=True)

    def test_bundle_validates(self):
        result = self.run_script("validate_bundle.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_skill_starts_with_qa_and_mode_routing(self):
        skill = (ROOT / "skills/product-studio/SKILL.md").read_text()
        for phrase in ["What do you want to build or improve?", "Hackathon", "Indie App", "SaaS", "Startup", "wait for explicit confirmation"]:
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
        self.assertEqual(state["approval_status"], "self_review_only")
        self.assertEqual(state["phases"]["product"]["status"], "blocked")
        record_review(state, "product", "independent", True, [])
        checkpoint(state, "product")
        self.assertEqual(state["approval_status"], "approved")
        self.assertEqual(state["phases"]["product"]["status"], "checkpointed")

    def test_workflow_runner_repair_iteration_and_next_phase(self):
        state = new_state("demo")
        begin_phase(state, "product")
        record_review(state, "product", "independent", False, ["wedge too broad"])
        self.assertEqual(state["iteration_count"], 1)
        self.assertEqual(state["next_action"], "repair-highest-impact-gap")
        record_review(state, "product", "independent", True, [])
        checkpoint(state, "product")
        self.assertEqual(state["next_action"], "begin-research")

    def test_workbench_detection_and_local_fallback(self):
        self.assertEqual(detect()["status"], "unavailable")
        with tempfile.TemporaryDirectory() as directory:
            target = publish_local(Path(directory), {"phase": "product"})
            self.assertTrue(target.exists())
            self.assertIn("local_fallback", target.read_text())


if __name__ == "__main__":
    unittest.main()
