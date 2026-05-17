import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
APP_PAGE = ROOT / "frontend" / "src" / "App.tsx"
MODELS_PAGE = ROOT / "frontend" / "src" / "pages" / "ModelsPage.tsx"
SETTINGS_PAGE = ROOT / "frontend" / "src" / "pages" / "SettingsPage.tsx"
HOME_PAGE = ROOT / "frontend" / "src" / "pages" / "HomePage.tsx"


class UiSourceSmokeTests(unittest.TestCase):
    def test_models_page_contains_delete_and_collapse_controls(self):
        content = MODELS_PAGE.read_text(encoding="utf-8")

        self.assertIn("Collapse all", content)
        self.assertIn("Expand all", content)
        self.assertIn("Delete", content)
        self.assertIn("Pokrecem model akciju", content)
        self.assertIn("Ukloni iz liste", content)
        self.assertIn("Obriši sa diska", content)

    def test_settings_page_mentions_scope_for_model_specific_settings(self):
        content = SETTINGS_PAGE.read_text(encoding="utf-8")

        self.assertIn("Settings scope", content)
        self.assertIn("Global defaults", content)
        self.assertIn("Active model override", content)
        self.assertIn("Access mode", content)
        self.assertIn("Tailscale", content)
        self.assertIn("TurboQuant preseti", content)
        self.assertIn("safe", content)
        self.assertIn("daily", content)
        self.assertIn("max-context", content)
        self.assertIn("Sacuvaj trenutni preset", content)
        self.assertIn("TurboQuant parametri", content)
        self.assertIn("Load preset", content)

    def test_home_page_contains_runtime_switch_controls(self):
        content = HOME_PAGE.read_text(encoding="utf-8")

        self.assertIn("Koristi llama.cpp", content)
        self.assertIn("Koristi TurboQuant", content)
        self.assertIn("Dostupni runtime-i", content)
        self.assertIn("Status runtime servera", content)

    def test_app_header_uses_host_platform_instead_of_ubuntu_literal(self):
        content = APP_PAGE.read_text(encoding="utf-8")

        self.assertIn("hostShellLabel", content)
        self.assertIn("hostPlatformLabel", content)
        self.assertNotIn("Ubuntu desktop", content)
        self.assertNotIn("Ubuntu Desktop GUI Shell", content)

    def test_models_page_mentions_unsloth_recommendations(self):
        content = MODELS_PAGE.read_text(encoding="utf-8")

        self.assertIn("Unsloth GGUF preporuke", content)
        self.assertIn("Dodaj Unsloth model", content)
        self.assertIn("Unsloth modeli", content)
        self.assertIn("Qwen3.6 35B A3B", content)
        self.assertIn("Qwen3.6 27B", content)
        self.assertIn("UD-IQ2_M", content)
        self.assertIn("UD-IQ3_XXS", content)
        self.assertNotIn("Koristi u HF formi", content)
        self.assertIn("Popuni repo i tacan GGUF filename", content)
        self.assertNotIn("disabled={!hfRepo.trim() || !hfFilename.trim()}", content)
        self.assertNotIn("disabled={!unslothRepo.trim() || !unslothFilename.trim()}", content)
        self.assertIn("action: \"pick-local-gguf\"", content)


if __name__ == "__main__":
    unittest.main()
