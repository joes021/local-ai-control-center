import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class WindowsInstallerBuilderTests(unittest.TestCase):
    def test_windows_builder_targets_next_repo_assets(self):
        content = (ROOT / "packaging" / "windows" / "build-setup.ps1").read_text(encoding="utf-8")
        self.assertIn("local-qwen-control-center-next", content)
        self.assertIn("Local AI Control Center", content)
        self.assertIn("Local-AI-Control-Center-Setup", content)


if __name__ == "__main__":
    unittest.main()
