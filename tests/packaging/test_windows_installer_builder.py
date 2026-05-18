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
        self.assertIn("install-summary.txt", content)
        self.assertIn("support\\launcher\\windows", content)

    def test_windows_installer_script_invokes_legacy_core_install(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("legacy", content.lower())
        self.assertIn("Local Qwen 3.635Ba3B on home computer", content)
        self.assertIn("control-center-next", content)
        self.assertIn("Start-LegacyRuntimeIfNeeded", content)
        self.assertIn("Write-InstallSummary", content)
        self.assertIn("support\\launcher\\windows", content)

    def test_windows_launcher_honors_access_mode_and_force_restart(self):
        content = (ROOT / "launchers" / "windows" / "start-control-center-next.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-RequestedAccessMode", content)
        self.assertIn("Get-RequestedHost", content)
        self.assertIn("CONTROL_CENTER_NEXT_FORCE_RESTART", content)
        self.assertIn("runtime-config.json", content)


if __name__ == "__main__":
    unittest.main()
