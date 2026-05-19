import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
APP_PAGE = ROOT / "frontend" / "src" / "App.tsx"
BROWSER_PAGE = ROOT / "frontend" / "src" / "pages" / "BrowserPage.tsx"
MODELS_PAGE = ROOT / "frontend" / "src" / "pages" / "ModelsPage.tsx"
SETTINGS_PAGE = ROOT / "frontend" / "src" / "pages" / "SettingsPage.tsx"
HOME_PAGE = ROOT / "frontend" / "src" / "pages" / "HomePage.tsx"
SERVER_PAGE = ROOT / "frontend" / "src" / "pages" / "ServerPage.tsx"
OPENCODE_PAGE = ROOT / "frontend" / "src" / "pages" / "OpenCodePage.tsx"
COMPAT_MODAL = ROOT / "frontend" / "src" / "components" / "CompatibilityCalculatorModal.tsx"
DOWNLOAD_PROGRESS_CARD = ROOT / "frontend" / "src" / "components" / "ModelDownloadProgressCard.tsx"


class UiSourceSmokeTests(unittest.TestCase):
    def test_models_page_contains_delete_and_collapse_controls(self):
        content = MODELS_PAGE.read_text(encoding="utf-8")
        download_card = DOWNLOAD_PROGRESS_CARD.read_text(encoding="utf-8")

        self.assertIn("Collapse all", content)
        self.assertIn("Expand all", content)
        self.assertIn("Svi", content)
        self.assertIn("Skinuti", content)
        self.assertIn("Aktivni", content)
        self.assertIn("Rezultati filtera", content)
        self.assertIn("ModelDownloadProgressCard", content)
        self.assertIn("Download status", download_card)
        self.assertIn("ETA", download_card)
        self.assertIn("Delete", content)
        self.assertIn("Check compatibility", content)
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
        self.assertIn("TURBOQUANT_DRAFT_STORAGE_KEY", content)
        self.assertIn("Save model settings", content)
        self.assertIn("Restore default", content)
        self.assertNotIn("Step mapping", content)
        self.assertNotIn("<select", content)

    def test_home_page_contains_runtime_switch_controls(self):
        content = HOME_PAGE.read_text(encoding="utf-8")

        self.assertIn("Koristi llama.cpp", content)
        self.assertIn("Koristi TurboQuant", content)
        self.assertIn("Dostupni runtime-i", content)
        self.assertIn("Status runtime servera", content)
        self.assertIn("Control Center health", content)
        self.assertIn("Server summary", content)
        self.assertIn("Runtime summary", content)
        self.assertIn("Binar u upotrebi", content)
        self.assertIn("TurboQuant detalji", content)
        self.assertIn("Local URL", content)
        self.assertIn("Tailscale URL", content)
        self.assertNotIn('label="Verzija"', content)
        self.assertNotIn('label="Access mode"', content)
        self.assertNotIn("Start llama.cpp server", content)
        self.assertNotIn("Stop llama.cpp server", content)
        self.assertNotIn("Run llama.cpp web", content)
        self.assertIn("Open OpenCode", content)
        self.assertIn("OpenCode config", content)
        self.assertIn("Promena modela vazi za novi OpenCode session", content)
        self.assertIn("Instanci:", content)

    def test_opencode_page_uses_old_control_center_labels(self):
        content = OPENCODE_PAGE.read_text(encoding="utf-8")

        self.assertIn("OpenCode stanje", content)
        self.assertIn("Instanci:", content)
        self.assertIn("Profil:", content)
        self.assertIn("Security režim:", content)
        self.assertIn("Autonomija:", content)
        self.assertIn("Ogranicen agent sa blacklist pravilima", content)
        self.assertIn("Potpuno otvoren agent", content)
        self.assertIn("4. Citanje + izmena + komande bez potvrde", content)
        self.assertIn("OpenCode steps", content)
        self.assertIn("Aktivni preset:", content)
        self.assertIn("Load preset", content)
        self.assertIn("Save preset", content)
        self.assertIn("Delete preset", content)
        self.assertIn("Restore default", content)

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
        self.assertIn('opencode: "OpenCode"', content)
        self.assertIn('browser: "Browser"', content)
        self.assertIn('benchmark: "Benchmark"', content)
        self.assertNotIn("Ubuntu desktop", content)
        self.assertNotIn("Ubuntu Desktop GUI Shell", content)

    def test_browser_page_contains_required_catalog_strings(self):
        content = BROWSER_PAGE.read_text(encoding="utf-8")
        download_card = DOWNLOAD_PROGRESS_CARD.read_text(encoding="utf-8")

        self.assertIn("Browser", content)
        self.assertIn("Search", content)
        self.assertIn("Refresh from internet", content)
        self.assertIn("Refresh Hugging Face", content)
        self.assertIn("Refresh Unsloth", content)
        self.assertIn("Fit", content)
        self.assertIn("Check compatibility", content)
        self.assertIn("Add to local catalog", content)
        self.assertIn("Catalog warnings", content)
        self.assertIn("Expand warnings", content)
        self.assertIn("Hugging Face", content)
        self.assertIn("browser-source-cell", content)
        self.assertIn("browser-source-text", content)
        self.assertIn("selectedItem ? (", content)
        self.assertIn("browser-detail-top", content)
        self.assertIn("rowsPerPage", content)
        self.assertIn("currentPage", content)
        self.assertIn("25", content)
        self.assertIn("browser-pagination", content)
        self.assertIn("ModelDownloadProgressCard", content)
        self.assertIn("Download status", download_card)
        self.assertIn("fetchDownloadProgress", content)
        self.assertIn("download-progress-track", download_card)
        self.assertIn("download-progress-fill", download_card)
        self.assertIn("/api/browser/catalog/download", (ROOT / "frontend" / "src" / "lib" / "api.ts").read_text(encoding="utf-8"))
        self.assertIn("Open model page", content)
        self.assertIn("<a", content)
        self.assertIn("sourceUrl", content)
        self.assertIn("record.repoId", content)
        self.assertNotIn("<aside className=\"browser-detail-panel\">", content)

    def test_compatibility_modal_contains_live_calculator_actions(self):
        content = COMPAT_MODAL.read_text(encoding="utf-8")

        self.assertIn("Compatibility calculator", content)
        self.assertIn("Expand advanced", content)
        self.assertIn("Apply package", content)
        self.assertIn("Re-check", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("Context pressure", content)
        self.assertIn("VRAM", content)
        self.assertIn("RAM", content)

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
        self.assertIn("Live input tok/s", benchmark_page)
        self.assertIn("Live output tok/s", benchmark_page)
        self.assertIn("Live ukupno tok/s", benchmark_page)
        self.assertIn("Avg input tok/s", benchmark_page)
        self.assertIn("Avg output tok/s", benchmark_page)
        self.assertIn("Avg ukupno tok/s", benchmark_page)
        self.assertIn("liveCurrent", benchmark_page)
        self.assertIn("liveHistory", benchmark_page)
        self.assertIn("window.setInterval", benchmark_page)
        self.assertIn("5000", benchmark_page)
        self.assertIn('"1m"', benchmark_page)
        self.assertIn('"5m"', benchmark_page)
        self.assertIn('"15m"', benchmark_page)
        self.assertIn('"1h"', benchmark_page)
        self.assertIn("benchmark-chart-status", benchmark_page)
        self.assertIn("benchmark-metric-value-input", benchmark_page)
        self.assertIn("benchmark-metric-value-output", benchmark_page)
        self.assertIn("benchmark-metric-value-total", benchmark_page)
        self.assertIn("nema novih zahteva u poslednjih", benchmark_page)
        self.assertIn("poslednji throughput:", benchmark_page)
        self.assertIn("live | poslednji throughput:", benchmark_page)
        self.assertIn("setSelectedRangeKey", benchmark_page)
        self.assertIn("strokeDasharray", benchmark_page)
        self.assertIn("<circle", benchmark_page)
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
        self.assertIn("Clear benchmark values", benchmark_page)
        self.assertIn("clearBenchmarkHistory", benchmark_page)
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
        self.assertIn(".benchmark-metric-value-input", styles)
        self.assertIn(".benchmark-metric-value-output", styles)
        self.assertIn(".benchmark-metric-value-total", styles)


if __name__ == "__main__":
    unittest.main()
