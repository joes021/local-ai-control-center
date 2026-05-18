import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class LinuxInstallerPayloadTests(unittest.TestCase):
    def test_linux_builder_mentions_both_architectures(self):
        content = (ROOT / "packaging" / "linux" / "build-run-installer.sh").read_text(encoding="utf-8")
        self.assertIn("x86_64", content)
        self.assertIn("arm64", content)
        self.assertIn("Local-AI-Control-Center-Setup-linux-", content)

    def test_linux_gui_installer_mentions_unified_choices_and_arm64_turbo_block(self):
        content = (ROOT / "install" / "linux" / "installer-gui.sh").read_text(encoding="utf-8")
        self.assertIn("Unified", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("arm64", content)
        self.assertIn("tailscale", content)

    def test_linux_installer_invokes_legacy_core_install_and_next_overlay(self):
        content = (ROOT / "install" / "linux" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("legacy", content.lower())
        self.assertIn("Local Qwen 3.635Ba3B on home computer", content)
        self.assertIn("control-center-next", content)
        self.assertIn("Control Center URL", content)
        self.assertIn("runtime-state.json", content)
        self.assertIn("read_runtime_port", content)
        self.assertIn("stop_existing_control_center_service", content)
        self.assertIn("systemctl --user stop control-center-next", content)
        self.assertIn("CONTROL_CENTER_NEXT_SKIP_OPEN=1", content)
        self.assertIn('CONTROL_CENTER_NEXT_ACCESS_MODE="$ACCESS_MODE"', content)

    def test_linux_launcher_uses_local_qwen_home_state(self):
        content = (ROOT / "launchers" / "linux" / "start-control-center-next.sh").read_text(encoding="utf-8")
        self.assertIn("LOCAL_QWEN_HOME_ROOT", content)
        self.assertIn('STATE_DIR="$LOCAL_QWEN_HOME_ROOT/state"', content)
        self.assertIn("SKIP_OPEN", content)
        self.assertIn("can_open_browser", content)


if __name__ == "__main__":
    unittest.main()
