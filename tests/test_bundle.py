from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


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
            self.assertTrue((state.parent / "artifacts").is_dir())

    def test_install_and_uninstall_are_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            result = self.run_script("install.py", "--target", "agents", "--destination", str(destination))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((destination / "product-studio" / "SKILL.md").exists())
            result = self.run_script("install.py", "--target", "agents", "--destination", str(destination), "--uninstall")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((destination / "product-studio").exists())

    def test_local_github_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issues = root / "issues.json"
            issues.write_text(json.dumps([{"title": "Build core flow", "body": "Acceptance criteria"}]))
            output = root / "github"
            result = self.run_script("export_github_plan.py", str(issues), "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("local_only", (output / "issue-plan.yaml").read_text())
            self.assertIn("Build core flow", (output / "issue-plan.md").read_text())


if __name__ == "__main__":
    unittest.main()
