import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "launchers" / "linux" / "install-desktop-entry.sh"


class DesktopEntryScriptTests(unittest.TestCase):
    def test_desktop_entry_script_contains_expected_fields(self):
        content = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("[Desktop Entry]", content)
        self.assertIn("Local AI Control Center", content)
        self.assertIn("start-control-center-next.sh", content)
        self.assertIn("Terminal=false", content)
        self.assertIn("local-qwen-control-center.desktop", content)
        self.assertIn(".tui-backup", content)


if __name__ == "__main__":
    unittest.main()
