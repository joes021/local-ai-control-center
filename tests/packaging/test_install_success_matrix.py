import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class InstallSuccessMatrixTests(unittest.TestCase):
    def test_windows_installer_declares_required_components(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("Control Center", content)
        self.assertIn("llama.cpp", content)
        self.assertIn("OpenCode", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("Runtime port", content)
        self.assertIn("Control Center startup", content)
        self.assertIn('$turboQuantRequired = -not $SkipTurboQuant', content)
        self.assertIn('if ($turboQuantRequired -and -not $components.turboQuantRuntime.ok) { $failedCore += "TurboQuant" }', content)

    def test_linux_installer_declares_arm64_optional_turboquant(self):
        content = (ROOT / "install" / "linux" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("python3", content)
        self.assertIn("node", content)
        self.assertIn("OpenCode", content)
        self.assertIn("llama.cpp", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("arm64", content)


if __name__ == "__main__":
    unittest.main()
