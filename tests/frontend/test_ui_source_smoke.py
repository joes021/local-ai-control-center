import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
APP_PAGE = ROOT / "frontend" / "src" / "App.tsx"
MODELS_PAGE = ROOT / "frontend" / "src" / "pages" / "ModelsPage.tsx"
SETTINGS_PAGE = ROOT / "frontend" / "src" / "pages" / "SettingsPage.tsx"
HOME_PAGE = ROOT / "frontend" / "src" / "pages" / "HomePage.tsx"
SERVER_PAGE = ROOT / "frontend" / "src" / "pages" / "ServerPage.tsx"


class UiSourceSmokeTests(unittest.TestCase):
    def test_models_page_contains_delete_and_collapse_controls(self):
        content = MODELS_PAGE.read_text(encoding="utf-8")

        self.assertIn("Collapse all", content)
        self.assertIn("Expand all", content)
        self.assertIn("Svi", content)
        self.assertIn("Skinuti", content)
        self.assertIn("Aktivni", content)
        self.assertIn("Rezultati filtera", content)
        self.assertIn("Download status", content)
        self.assertIn("ETA", content)
        self.assertIn("Delete", content)
        self.assertIn("Pokrecem model akciju", content)
        self.assertIn("Ukloni iz liste", content)
        self.assertIn("Obrisi", content)
        self.assertIn("MTP status", content)
        self.assertIn("Bez MTP", content)
        self.assertIn("Ima MTP", content)
        self.assertIn("Nepoznato MTP", content)

    def test_settings_page_mentions_scope_for_model_specific_settings(self):
        content = SETTINGS_PAGE.read_text(encoding="utf-8")

        self.assertIn("Settings scope", content)
        self.assertIn("CustomSelect", content)
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
        self.assertIn("OpenCode config", content)
        self.assertIn("Security mode", content)
        self.assertIn("Capability mode", content)
        self.assertIn("Save OpenCode settings", content)
        self.assertNotIn("<select", content)

    def test_home_page_contains_runtime_switch_controls(self):
        content = HOME_PAGE.read_text(encoding="utf-8")

        self.assertIn("Koristi llama.cpp", content)
        self.assertIn("Koristi TurboQuant", content)
        self.assertIn("Dostupni runtime-i", content)
        self.assertIn("Status runtime servera", content)
        self.assertIn("Server status", content)
        self.assertIn("Server health", content)
        self.assertNotIn("Start llama.cpp server", content)
        self.assertNotIn("Stop llama.cpp server", content)
        self.assertNotIn("Run llama.cpp web", content)
        self.assertIn("Open OpenCode", content)
        self.assertIn("OpenCode config", content)
        self.assertIn("Promena modela vazi za novi OpenCode session", content)

    def test_server_page_contains_server_actions_and_detailed_status(self):
        content = SERVER_PAGE.read_text(encoding="utf-8")

        self.assertIn("llama.cpp server", content)
        self.assertIn("Start llama.cpp server", content)
        self.assertIn("Stop llama.cpp server", content)
        self.assertIn("Run llama.cpp web", content)
        self.assertIn("Server status", content)
        self.assertIn("Server health", content)
        self.assertIn("Server PID", content)
        self.assertIn("Poslednja poruka", content)
        self.assertIn("Tailscale web", content)

    def test_app_header_uses_host_platform_instead_of_ubuntu_literal(self):
        content = APP_PAGE.read_text(encoding="utf-8")

        self.assertIn("hostShellLabel", content)
        self.assertIn("hostPlatformLabel", content)
        self.assertIn("Local AI Control Center", content)
        self.assertIn("status?.version", content)
        self.assertIn('server: "Server"', content)
        self.assertIn('benchmark: "Benchmark"', content)
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
        self.assertIn("Ako je OpenCode vec otvoren, zatvori ga i otvori ponovo", content)
        self.assertNotIn("disabled={!hfRepo.trim() || !hfFilename.trim()}", content)
        self.assertNotIn("disabled={!unslothRepo.trim() || !unslothFilename.trim()}", content)
        self.assertIn('action: "pick-local-gguf"', content)

    def test_updates_page_mentions_progress_and_installer_behavior(self):
        updates_page = (ROOT / "frontend" / "src" / "pages" / "UpdatesPage.tsx").read_text(
            encoding="utf-8"
        )

        self.assertIn("Update status", updates_page)
        self.assertIn("Procenat", updates_page)
        self.assertIn("ETA", updates_page)
        self.assertIn("Pokretanje installera", updates_page)
        self.assertIn("Sledeci korak", updates_page)
        self.assertIn("Release URL", updates_page)
        self.assertIn("Install update", updates_page)

    def test_benchmark_page_contains_live_throughput_and_graph_markers(self):
        benchmark_page = (ROOT / "frontend" / "src" / "pages" / "BenchmarkPage.tsx").read_text(
            encoding="utf-8"
        )
        app_page = APP_PAGE.read_text(encoding="utf-8")

        self.assertIn("Benchmark", app_page)
        self.assertIn("LIVE THROUGHPUT", benchmark_page)
        self.assertIn("Benchmark grafikon", benchmark_page)
        self.assertIn("Request activity", benchmark_page)
        self.assertIn("Input tok/s", benchmark_page)
        self.assertIn("Output tok/s", benchmark_page)
        self.assertIn("Ukupno tok/s", benchmark_page)
        self.assertIn("window.setInterval", benchmark_page)
        self.assertIn("5000", benchmark_page)
        self.assertNotIn("Y osa: tok/s", benchmark_page)
        self.assertNotIn("X osa: skoriji zahtevi sleva nadesno", benchmark_page)
        self.assertIn("Legenda", benchmark_page)
        self.assertIn("Otvori puni live log", benchmark_page)
        self.assertIn("Zadnjih 30 linija", benchmark_page)
        self.assertIn("Run selected test", benchmark_page)
        self.assertIn("Run full battery", benchmark_page)
        self.assertIn("Save battery", benchmark_page)
        self.assertIn("Load battery", benchmark_page)
        self.assertIn("Restore default tests", benchmark_page)
        self.assertIn("queued", benchmark_page)
        self.assertIn("running", benchmark_page)
        self.assertIn("done", benchmark_page)
        self.assertIn("failed", benchmark_page)
        self.assertIn("Benchmark istorija", benchmark_page)
        self.assertIn("battery-scenario-list", benchmark_page)
        self.assertIn("battery-editor-detail", benchmark_page)
        self.assertIn("benchmark-run-summary", benchmark_page)
        self.assertIn("scenario-status-badge", benchmark_page)
        self.assertIn("CustomSelect", benchmark_page)
        self.assertNotIn("<select", benchmark_page)

    def test_global_styles_force_dark_form_controls_and_scrollbars(self):
        styles = (ROOT / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("color-scheme: dark", styles)
        self.assertIn(".status-card option", styles)
        self.assertIn("input:-webkit-autofill", styles)
        self.assertIn("::-webkit-scrollbar", styles)
        self.assertIn(".status-card input:not([type])", styles)
        self.assertIn(".custom-select-trigger", styles)
        self.assertIn(".custom-select-menu", styles)
        self.assertIn(".custom-select-option-selected", styles)
        self.assertIn(".status-card:has(.custom-select-open)", styles)
        self.assertIn(".custom-select-open", styles)


if __name__ == "__main__":
    unittest.main()
