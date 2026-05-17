import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "launchers" / "linux" / "start-control-center-next.sh"


class LinuxLauncherSmokeTests(unittest.TestCase):
    def test_launcher_contains_expected_flow_markers(self):
        content = LAUNCHER.read_text(encoding="utf-8")

        self.assertIn("127.0.0.1", content)
        self.assertIn("3210", content)
        self.assertIn("xdg-open", content)
        self.assertIn("/api/health", content)
        self.assertIn("npm run build", content)
        self.assertIn("CONTROL_CENTER_NEXT_UI_PORT", content)
        self.assertIn("select_first_free_port", content)
        self.assertIn("systemd-run --user", content)
        self.assertIn("reuse_existing_backend", content)


if __name__ == "__main__":
    unittest.main()
