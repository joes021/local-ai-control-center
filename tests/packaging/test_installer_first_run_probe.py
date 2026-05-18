import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class InstallerFirstRunProbeTests(unittest.TestCase):
    def test_windows_installer_declares_first_run_probe_contract(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("firstRunProbe", content)
        self.assertIn("probeReady", content)
        self.assertIn("probePrompt", content)
        self.assertIn("Reply with exactly OK and nothing else.", content)
        self.assertIn("first-run probe", content.lower())

    def test_windows_installer_gates_success_on_first_run_probe(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("first-run probe", content.lower())
        self.assertIn("probeReady", content)
        self.assertIn("firstRunProbe", content)

    def test_linux_installer_declares_first_run_probe_contract(self):
        content = (ROOT / "install" / "linux" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("firstRunProbe", content)
        self.assertIn("probeReady", content)
        self.assertIn("probePrompt", content)
        self.assertIn("Reply with exactly OK and nothing else.", content)
        self.assertIn("first-run probe", content.lower())

    def test_linux_installer_gates_success_on_first_run_probe(self):
        content = (ROOT / "install" / "linux" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("firstRunProbe", content)
        self.assertIn("probeReady", content)
        self.assertIn("first-run probe", content.lower())
        self.assertIn("reasoning_content", content)
        self.assertIn("completion_tokens", content)
        self.assertIn("ready-non-exact", content)

    def test_windows_installer_accepts_reasoning_only_probe_output(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("reasoning_content", content)
        self.assertIn("completion_tokens", content)
        self.assertIn("ready-non-exact", content)


if __name__ == "__main__":
    unittest.main()
