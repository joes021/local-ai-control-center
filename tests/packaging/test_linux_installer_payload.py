import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class LinuxInstallerPayloadTests(unittest.TestCase):
    def test_linux_builder_mentions_both_architectures(self):
        content = (ROOT / "packaging" / "linux" / "build-run-installer.sh").read_text(encoding="utf-8")
        self.assertIn("x86_64", content)
        self.assertIn("arm64", content)
        self.assertIn("Local-AI-Control-Center-Setup-linux-", content)


if __name__ == "__main__":
    unittest.main()
