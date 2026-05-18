import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class WindowsInstallerBuilderTests(unittest.TestCase):
    def test_windows_builder_targets_next_repo_assets(self):
        content = (ROOT / "packaging" / "windows" / "build-setup.ps1").read_text(encoding="utf-8")
        self.assertIn("local-qwen-control-center-next", content)
        self.assertIn("Local AI Control Center", content)
        self.assertIn("Local-AI-Control-Center-Setup", content)

    def test_windows_inno_setup_mentions_unified_installer_choices(self):
        content = (ROOT / "packaging" / "windows" / "LocalAIControlCenterSetup.iss").read_text(encoding="utf-8")
        self.assertIn("Access mode", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("OpenCode", content)
        self.assertIn("Unified", content)

    def test_windows_installer_script_invokes_legacy_core_install(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("legacy", content.lower())
        self.assertIn("Local Qwen 3.635Ba3B on home computer", content)
        self.assertIn("control-center-next", content)


if __name__ == "__main__":
    unittest.main()
