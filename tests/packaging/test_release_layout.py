import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ReleaseLayoutTests(unittest.TestCase):
    def test_packaging_layout_exists(self):
        self.assertTrue((ROOT / "packaging" / "windows" / "build-setup.ps1").exists())
        self.assertTrue((ROOT / "packaging" / "windows" / "LocalAIControlCenterSetup.iss").exists())
        self.assertTrue((ROOT / "packaging" / "linux" / "build-run-installer.sh").exists())
        self.assertTrue((ROOT / "packaging" / "release-all.ps1").exists())

    def test_release_automation_mentions_three_primary_artifacts(self):
        content = (ROOT / "packaging" / "release-all.ps1").read_text(encoding="utf-8")
        self.assertIn("Local-AI-Control-Center-Setup-", content)
        self.assertIn("linux-x86_64", content)
        self.assertIn("linux-arm64", content)
        self.assertIn("checksums.txt", content)
        self.assertIn("support-matrix.json", content)
        self.assertIn("releaseUrl", content)
        self.assertIn("generatedAt", content)

    def test_readme_download_links_follow_current_version(self):
        version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"releases/tag/v{version}", content)
        self.assertIn(f"Local-AI-Control-Center-Setup-{version}.exe", content)
        self.assertIn(f"Local-AI-Control-Center-Setup-linux-x86_64-{version}.run", content)
        self.assertIn(f"Local-AI-Control-Center-Setup-linux-arm64-{version}.run", content)
        self.assertNotIn("v2.24.2", content)

    def test_getting_started_links_follow_current_version(self):
        version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
        content = (ROOT / "docs" / "GETTING_STARTED.md").read_text(encoding="utf-8")
        self.assertIn(f"releases/tag/v{version}", content)
        self.assertNotIn("v2.24.2", content)


if __name__ == "__main__":
    unittest.main()
