import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class InstallerFirstRunReadinessTests(unittest.TestCase):
    def test_windows_installer_declares_model_bootstrap_contract(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("modelBootstrap", content)
        self.assertIn("bootstrapReady", content)
        self.assertIn("selectedModelDownloaded", content)
        self.assertIn("selected model selection", content.lower())
        self.assertIn("model bootstrap", content.lower())

    def test_linux_installer_declares_model_bootstrap_contract(self):
        content = (ROOT / "install" / "linux" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("modelBootstrap", content)
        self.assertIn("bootstrapReady", content)
        self.assertIn("selectedModelDownloaded", content)
        self.assertIn("model bootstrap", content.lower())
        self.assertIn("download_selected_model_direct", content)
        self.assertIn("huggingface_hub", content)
        self.assertIn('repo = str(entry.get("repo"', content)
        self.assertIn('filename = str(entry.get("downloadFile"', content)
        self.assertIn('if bootstrap_payload.get("selectedModelDownloaded") and bootstrap_payload.get("selectedModelPath") and not model_file:', content)
        self.assertIn('selected_model_file = Path(model_file).name', content)

    def test_models_service_exposes_installer_bootstrap_readiness_helper(self):
        from backend.app.services import models_service

        self.assertTrue(hasattr(models_service, "resolve_installer_selected_model"))
        self.assertTrue(hasattr(models_service, "build_installer_bootstrap_readiness"))


if __name__ == "__main__":
    unittest.main()
