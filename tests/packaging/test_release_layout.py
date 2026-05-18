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


if __name__ == "__main__":
    unittest.main()
