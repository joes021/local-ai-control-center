import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class LinuxInstallerPayloadTests(unittest.TestCase):
    def test_linux_builder_mentions_both_architectures(self):
        content = (ROOT / "packaging" / "linux" / "build-run-installer.sh").read_text(encoding="utf-8")
        self.assertIn("x86_64", content)
        self.assertIn("arm64", content)
        self.assertIn("Local-AI-Control-Center-Setup-linux-", content)

    def test_linux_gui_installer_mentions_unified_choices_and_arm64_turbo_block(self):
        content = (ROOT / "install" / "linux" / "installer-gui.sh").read_text(encoding="utf-8")
        self.assertIn("Unified", content)
        self.assertIn("TurboQuant", content)
        self.assertIn("arm64", content)
        self.assertIn("tailscale", content)
        self.assertIn("recommended-models.json", content)
        self.assertIn("defaultModelId", content)
        self.assertIn("MODEL_ID", content)
        self.assertIn("Prikazi jos modela", content)
        self.assertIn("gemma-4-e4b-it-q4-0", content)
        self.assertIn("qwen3.6-35b-a3b-ud-iq2-xxs", content)
        self.assertIn("qwen3.6-35b-a3b-mtp-ud-q4-k-xl", content)
        self.assertNotIn("Preuzmi preporuceni model odmah?", content)
        self.assertNotIn("bootstrap handoff", content.lower())
        self.assertNotIn("bootstrap/download", content.lower())

    def test_linux_tui_installer_mentions_guided_model_selection(self):
        content = (ROOT / "install" / "linux" / "installer-tui.sh").read_text(encoding="utf-8")
        self.assertIn("recommended-models.json", content)
        self.assertIn("defaultModelId", content)
        self.assertIn("MODEL_ID", content)
        self.assertIn("Prikazi jos modela", content)
        self.assertIn("gemma-4-e4b-it-q4-0", content)
        self.assertIn("qwen3.6-35b-a3b-ud-iq2-xxs", content)
        self.assertIn("qwen3.6-35b-a3b-mtp-ud-q4-k-xl", content)
        self.assertNotIn("Download model now?", content)
        self.assertNotIn("bootstrap handoff", content.lower())
        self.assertNotIn("bootstrap/download", content.lower())

    def test_linux_installer_invokes_legacy_core_install_and_next_overlay(self):
        content = (ROOT / "install" / "linux" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("legacy", content.lower())
        self.assertIn("Local Qwen 3.635Ba3B on home computer", content)
        self.assertIn("control-center-next", content)
        self.assertIn("Control Center URL", content)
        self.assertIn("runtime-state.json", content)
        self.assertIn("read_runtime_port", content)
        self.assertIn("stop_existing_control_center_service", content)
        self.assertIn("systemctl --user stop control-center-next", content)
        self.assertIn("CONTROL_CENTER_NEXT_SKIP_OPEN=1", content)
        self.assertIn('CONTROL_CENTER_NEXT_ACCESS_MODE="$ACCESS_MODE"', content)
        self.assertIn("OPENCODE_WORKSPACE_DIR", content)
        self.assertIn("LEGACY_LAUNCHERS_PAYLOAD_DIR", content)
        self.assertIn('"workingDirectory": str(existing_settings.get("opencode", {}).get("workingDirectory", opencode_workspace) or opencode_workspace)', content)
        self.assertIn('"threads": int(existing_settings.get("threads", 8) or 8)', content)
        self.assertIn('"installRoot": str(workspace_root)', content)
        self.assertIn('SELECTED_MODEL_ID="${SELECTED_MODEL_ID:-}"', content)
        self.assertIn('SELECTED_MODEL_FILE="${SELECTED_MODEL_FILE:-}"', content)
        self.assertIn('"selectedModelId"', content)
        self.assertIn('"selectedModelFile"', content)
        self.assertIn("normalize_shell_scripts", content)
        self.assertIn('find "$APP_ROOT/launchers" "$APP_ROOT/install" "$BIN_DIR" -type f -name "*.sh" -exec chmod +x {} +', content)
        self.assertIn('if [ -x "$target/build/bin/llama-server" ]; then', content)
        self.assertIn('if [ "$SKIP_LLAMA_SETUP" = "1" ]; then', content)

    def test_linux_launcher_uses_local_qwen_home_state(self):
        content = (ROOT / "launchers" / "linux" / "start-control-center-next.sh").read_text(encoding="utf-8")
        self.assertIn("LOCAL_QWEN_HOME_ROOT", content)
        self.assertIn('STATE_DIR="$LOCAL_QWEN_HOME_ROOT/state"', content)
        self.assertIn("SKIP_OPEN", content)
        self.assertIn("can_open_browser", content)

    def test_linux_builder_packages_legacy_launchers(self):
        content = (ROOT / "packaging" / "linux" / "build-run-installer.sh").read_text(encoding="utf-8")
        self.assertIn('"$payload_dir/legacy-launchers"', content)
        self.assertIn('cp -R "$SUPPORT_REPO/launchers/." "$payload_dir/legacy-launchers/"', content)
        self.assertIn('replace(b"\\r\\n", b"\\n")', content)
        self.assertIn("resolve_python_cmd()", content)
        self.assertIn('PYTHON_CMD="$(resolve_python_cmd)"', content)
        self.assertIn('"$PYTHON_CMD" - <<\'PY\'', content)


if __name__ == "__main__":
    unittest.main()
