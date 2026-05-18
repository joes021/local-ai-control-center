import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class WindowsInstallerBuilderTests(unittest.TestCase):
    def test_windows_builder_targets_next_repo_assets(self):
        content = (ROOT / "packaging" / "windows" / "build-setup.ps1").read_text(encoding="utf-8")
        self.assertIn("local-qwen-control-center-next", content)
        self.assertIn("Local AI Control Center", content)
        self.assertIn("Local-AI-Control-Center-Setup", content)

    def test_windows_inno_setup_mentions_unified_installer_choices(self):
        content = (ROOT / "packaging" / "windows" / "LocalAIControlCenterSetup.iss").read_text(encoding="utf-8")
        self.assertIn("Access mode", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("OpenCode", content)
        self.assertIn("Unified", content)
        self.assertIn("Guided model selection", content)
        self.assertIn("Prikazi jos modela", content)
        self.assertIn("GetWizardFallbackDefaultModelId", content)
        self.assertIn("authoritative shared catalog is read later by install.ps1", content)
        self.assertNotIn("default follows defaultModelId from the shared catalog", content)
        self.assertIn("gemma-4-e4b-it-q4-0", content)
        self.assertIn("install-summary.txt", content)
        self.assertIn("support\\launcher\\windows", content)
        self.assertIn("function GetModelField(ModelIndex: Integer; FieldName: string): string;", content)
        self.assertIn("function GetSelectedModelIndex(): Integer;", content)
        self.assertIn("for modelIndex := 0 to GetModelOptionCount() - 1 do", content)
        self.assertNotIn("ModelSelectionPage.Values[1]", content)
        self.assertNotIn("ModelSelectionPage.Values[2]", content)
        self.assertEqual(content.count("FieldName = 'option'"), 3)

    def test_windows_installer_script_invokes_legacy_core_install(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("legacy", content.lower())
        self.assertIn("Local Qwen 3.635Ba3B on home computer", content)
        self.assertIn("control-center-next", content)
        self.assertIn("Start-LegacyRuntimeIfNeeded", content)
        self.assertIn("selectedModelId", content)
        self.assertIn("selectedModelDownloadFile", content)
        self.assertIn("defaultModelId", content)
        self.assertIn("Get-RecommendedModelCatalog", content)
        self.assertIn("recommended-models.json", content)
        self.assertIn("catalog-default", content)
        self.assertIn("Write-InstallSummary", content)
        self.assertIn("support\\launcher\\windows", content)
        self.assertIn("install.log", content)
        self.assertIn("Next step:", content)
        self.assertIn("$resolvedLabel = [string]$catalogEntry.label", content)
        self.assertIn("$resolvedDownloadFile = [string]$catalogEntry.downloadFile", content)
        catalog_block = content.split("if ($catalogEntry) {", 1)[1].split("if ([string]::IsNullOrWhiteSpace($resolvedLabel)) {", 1)[0]
        self.assertIn("$resolvedLabel = [string]$catalogEntry.label", catalog_block)
        self.assertIn("$resolvedDownloadFile = [string]$catalogEntry.downloadFile", catalog_block)
        self.assertIn("$resolvedVramClass = [string]$catalogEntry.vramClass.label", catalog_block)
        self.assertNotIn("IsNullOrWhiteSpace($resolvedLabel)", catalog_block)
        self.assertNotIn("IsNullOrWhiteSpace($resolvedDownloadFile)", catalog_block)

    def test_windows_installer_uses_catalog_as_authoritative_metadata_source(self):
        content = (ROOT / "install" / "windows" / "install.ps1").read_text(encoding="utf-8")
        self.assertIn("$selectionSource = \"wizard\"", content)
        self.assertIn("$selectionSource = \"catalog-default\"", content)
        self.assertIn("$selectionSource = \"catalog-fallback\"", content)
        self.assertIn("$catalogEntry = $catalog.recommended | Where-Object { $_.modelId -eq $resolvedModelId }", content)
        self.assertIn("if (-not $catalogEntry -and $resolvedModelId -ne $catalogDefaultModelId) {", content)
        self.assertIn("if ([string]::IsNullOrWhiteSpace($resolvedLabel)) {", content)
        self.assertIn("if ([string]::IsNullOrWhiteSpace($resolvedDownloadFile)) {", content)
        self.assertIn("if ([string]::IsNullOrWhiteSpace($resolvedVramClass)) {", content)

    def test_windows_launcher_honors_access_mode_and_force_restart(self):
        content = (ROOT / "launchers" / "windows" / "start-control-center-next.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-RequestedAccessMode", content)
        self.assertIn("Get-RequestedHost", content)
        self.assertIn("CONTROL_CENTER_NEXT_FORCE_RESTART", content)
        self.assertIn("runtime-config.json", content)


if __name__ == "__main__":
    unittest.main()
