import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class StatusServiceTests(unittest.TestCase):
    def test_build_status_payload_contains_home_screen_fields(self):
        from backend.app.services.local_qwen_state import build_status_payload

        payload = build_status_payload(
            {
                "version": "2.10.57",
                "health": "ok",
                "activeModel": "qwen36-35b-a3b-IQ2_M.gguf",
                "profile": "balanced",
            },
            ui_port=3210,
        )

        self.assertEqual(payload["version"], "2.10.57")
        self.assertEqual(payload["health"], "ok")
        self.assertEqual(payload["activeModel"], "qwen36-35b-a3b-IQ2_M.gguf")
        self.assertEqual(payload["profile"], "balanced")
        self.assertEqual(payload["uiPort"], 3210)
        self.assertEqual(payload["uiUrl"], "http://127.0.0.1:3210")
        self.assertIn("localUrl", payload)
        self.assertIn("tailscaleUrl", payload)
        self.assertIn("runtimeStatus", payload)
        self.assertIn("runtimeSummary", payload)
        self.assertIn("activeRuntimeLabel", payload)
        self.assertIn("availableRuntimes", payload)
        self.assertIn("turboQuantStatus", payload)
        self.assertIn("turboQuantReason", payload)
        self.assertIn("runtimeLiveStatus", payload)
        self.assertIn("runtimeLiveReason", payload)

    def test_runtime_summary_prefers_turbo_when_turbo_server_is_configured(self):
        from backend.app.services.local_qwen_state import load_runtime_summary

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            turbo = home / "apps" / "llama.cpp-turboquant" / "build-cuda" / "bin" / "llama-server"
            llama = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
            turbo.parent.mkdir(parents=True)
            llama.parent.mkdir(parents=True)
            turbo.write_text("turbo", encoding="utf-8")
            llama.write_text("llama", encoding="utf-8")
            (home / "state" / "install-state.json").write_text(
                f'{{"llamaServerExe":"{llama.as_posix()}","turboServerExe":"{turbo.as_posix()}"}}',
                encoding="utf-8",
            )
            (home / "state" / "install-report.json").write_text(
                '{"components":{"llamaCppRuntime":{"ok":true},"turboQuantRuntime":{"ok":true}}}',
                encoding="utf-8",
            )

            payload = load_runtime_summary(home)

            self.assertEqual(payload["active"], "turboquant")
            self.assertTrue(payload["turboAvailable"])
            self.assertEqual(payload["turboStatus"], "aktivan")

    def test_runtime_summary_reports_binary_in_use_from_running_process(self):
        from backend.app.services.local_qwen_state import load_runtime_summary

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            turbo = home / "apps" / "llama.cpp-turboquant" / "build-cuda" / "bin" / "llama-server"
            llama = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
            turbo.parent.mkdir(parents=True)
            llama.parent.mkdir(parents=True)
            turbo.write_text("turbo", encoding="utf-8")
            llama.write_text("llama", encoding="utf-8")
            (home / "state" / "install-state.json").write_text(
                f'{{"llamaServerExe":"{llama.as_posix()}","turboServerExe":"{turbo.as_posix()}"}}',
                encoding="utf-8",
            )
            (home / "state" / "install-report.json").write_text(
                '{"components":{"llamaCppRuntime":{"ok":true},"turboQuantRuntime":{"ok":true}}}',
                encoding="utf-8",
            )

            process_output = f"1234 {turbo.as_posix()} -m /tmp/model.gguf --port 8091\n"
            with patch("backend.app.services.local_qwen_state.subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = process_output
                run_mock.return_value.stderr = ""

                payload = load_runtime_summary(home)

            self.assertEqual(payload["activeBinary"], turbo.as_posix())
            self.assertEqual(payload["activeBinarySource"], "process")
            self.assertIn(payload["runtimeLiveStatus"], {"potvrđen kroz proces", "potvrđen kroz health"})


    def test_runtime_summary_uses_lifecycle_reason_when_health_and_process_are_missing(self):
        from backend.app.services.local_qwen_state import load_runtime_summary

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            turbo = home / "apps" / "llama.cpp-turboquant" / "build-cuda" / "bin" / "llama-server"
            llama = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
            turbo.parent.mkdir(parents=True)
            llama.parent.mkdir(parents=True)
            turbo.write_text("turbo", encoding="utf-8")
            llama.write_text("llama", encoding="utf-8")
            (home / "state" / "install-state.json").write_text(
                f'{{"llamaServerExe":"{llama.as_posix()}","turboServerExe":"{turbo.as_posix()}","port":8091}}',
                encoding="utf-8",
            )
            (home / "state" / "install-report.json").write_text(
                '{"components":{"llamaCppRuntime":{"ok":true},"turboQuantRuntime":{"ok":true}}}',
                encoding="utf-8",
            )
            (home / "state" / "server-lifecycle.json").write_text(
                '{"state":"inactive","reason":"Sacuvani lifecycle je tvrdio da je server aktivan, ali nisu pronadjeni ni health endpoint ni llama-server proces."}',
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.local_qwen_state.probe_runtime_health",
                return_value=("offline", "Health endpoint nije dostupan."),
            ):
                with patch(
                    "backend.app.services.local_qwen_state.detect_running_runtime_binary",
                    return_value="",
                ):
                    payload = load_runtime_summary(home)

            self.assertEqual(payload["runtimeLiveStatus"], "nije potvrđen")
            self.assertIn("Sacuvani lifecycle je tvrdio", payload["runtimeLiveReason"])

    def test_runtime_summary_normalizes_stale_active_lifecycle_without_health_or_process(self):
        from backend.app.services.local_qwen_state import load_runtime_summary

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            turbo = home / "apps" / "llama.cpp-turboquant" / "build-cuda" / "bin" / "llama-server"
            llama = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
            turbo.parent.mkdir(parents=True)
            llama.parent.mkdir(parents=True)
            turbo.write_text("turbo", encoding="utf-8")
            llama.write_text("llama", encoding="utf-8")
            (home / "state" / "install-state.json").write_text(
                f'{{"llamaServerExe":"{llama.as_posix()}","turboServerExe":"{turbo.as_posix()}","port":8091}}',
                encoding="utf-8",
            )
            (home / "state" / "install-report.json").write_text(
                '{"components":{"llamaCppRuntime":{"ok":true},"turboQuantRuntime":{"ok":true}}}',
                encoding="utf-8",
            )
            (home / "state" / "server-lifecycle.json").write_text(
                '{"state":"active","reason":"Health endpoint returned OK."}',
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.local_qwen_state.probe_runtime_health",
                return_value=("offline", "Health endpoint nije dostupan."),
            ):
                with patch(
                    "backend.app.services.local_qwen_state.detect_running_runtime_binary",
                    return_value="",
                ):
                    payload = load_runtime_summary(home)

            self.assertEqual(payload["runtimeLiveStatus"], "nije potvrđen")
            self.assertIn("Sacuvani lifecycle je tvrdio da je server aktivan", payload["runtimeLiveReason"])


if __name__ == "__main__":
    unittest.main()
