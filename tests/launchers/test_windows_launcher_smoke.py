import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "launchers" / "windows" / "start-control-center-next.ps1"
CHECKER = ROOT / "launchers" / "windows" / "check-backend.ps1"


class WindowsLauncherSmokeTests(unittest.TestCase):
    def test_windows_launcher_contains_expected_flow_markers(self):
        content = LAUNCHER.read_text(encoding="utf-8")

        self.assertIn("127.0.0.1", content)
        self.assertIn("3210", content)
        self.assertIn("/api/health", content)
        self.assertIn("CONTROL_CENTER_NEXT_UI_PORT", content)
        self.assertIn("CONTROL_CENTER_NEXT_TARGET_PLATFORM", content)
        self.assertIn("LOCAL_QWEN_HOME", content)
        self.assertIn("select_first_free_port", content)
        self.assertIn("Start-Process", content)
        self.assertIn("Start-Process $browserPath", content)
        self.assertIn("runtime-state.json", content)
        self.assertIn("run_control_center_next.py", content)
        self.assertIn("System.Threading.Mutex", content)
        self.assertIn("WaitOne", content)
        self.assertIn("ReleaseMutex", content)
        self.assertIn("Save-State -Port $Port -ProcessId $process.Id", content)

    def test_windows_backend_checker_hits_health_endpoint(self):
        content = CHECKER.read_text(encoding="utf-8")

        self.assertIn("/api/health", content)
        self.assertIn("Invoke-WebRequest", content)
        self.assertIn("127.0.0.1:3210", content)


if __name__ == "__main__":
    unittest.main()
