import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class ServerServiceTests(unittest.TestCase):
    def test_load_server_status_aggregates_lifecycle_health_and_runtime_data(self):
        from backend.app.services.server_service import load_server_status

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            (home / "state" / "install-state.json").write_text(
                json.dumps(
                    {
                        "modelId": "unsloth-Qwen3.6-35B-A3B-UD-IQ3_S.gguf",
                        "port": 8091,
                        "profile": "balanced",
                    }
                ),
                encoding="utf-8",
            )
            (home / "state" / "settings.json").write_text(
                json.dumps({"profile": "balanced"}),
                encoding="utf-8",
            )
            (home / "state" / "server-lifecycle.json").write_text(
                json.dumps(
                    {
                        "state": "active",
                        "reason": "Health endpoint returned OK.",
                        "updatedAt": "2026-05-17T18:22:00Z",
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.server_service.load_local_qwen_summary",
                return_value={
                    "activeModel": "unsloth-Qwen3.6-35B-A3B-UD-IQ3_S.gguf",
                    "profile": "balanced",
                    "runtime": {
                        "active": "turboquant",
                        "runtimeLiveStatus": "potvrdjen kroz health",
                        "runtimeLiveReason": "Runtime health endpoint odgovara.",
                    },
                },
            ) as summary_loader:
                with patch(
                    "backend.app.services.server_service.probe_runtime_health",
                    return_value=("ok", "Runtime health endpoint odgovara."),
                ):
                    with patch(
                        "backend.app.services.server_service.detect_server_pid",
                        return_value=4321,
                    ):
                        payload = load_server_status(local_qwen_home=home)

            summary_loader.assert_called_once_with(home)
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["port"], 8091)
            self.assertEqual(payload["health"], "ok")
            self.assertEqual(payload["pid"], 4321)
            self.assertFalse(payload["hasWarning"])
            self.assertEqual(payload["warningSeverity"], "")
            self.assertEqual(payload["warningSummary"], "")
            self.assertEqual(payload["activeModel"], "unsloth-Qwen3.6-35B-A3B-UD-IQ3_S.gguf")
            self.assertEqual(payload["activeRuntime"], "turboquant")
            self.assertEqual(payload["lastReason"], "Health endpoint returned OK.")
            self.assertEqual(payload["webUrl"], "http://127.0.0.1:8091/")
            self.assertEqual(payload["healthUrl"], "http://127.0.0.1:8091/health")

    def test_load_server_status_exposes_warning_summary_for_degraded_state(self):
        from backend.app.services.server_service import load_server_status

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            (home / "state" / "install-state.json").write_text(
                json.dumps({"port": 8091, "profile": "balanced"}),
                encoding="utf-8",
            )
            (home / "state" / "server-lifecycle.json").write_text(
                json.dumps(
                    {
                        "state": "active",
                        "reason": "Sacuvani lifecycle je tvrdio da je server aktivan, ali health ne odgovara.",
                        "updatedAt": "2026-05-17T18:22:00Z",
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.server_service.load_local_qwen_summary",
                return_value={
                    "activeModel": "demo.gguf",
                    "profile": "balanced",
                    "runtime": {
                        "active": "llama.cpp",
                        "runtimeLiveStatus": "nije potvrdjen",
                        "runtimeLiveReason": "Health endpoint nije dostupan.",
                    },
                },
            ):
                with patch(
                    "backend.app.services.server_service.probe_runtime_health",
                    return_value=("offline", "Health endpoint nije dostupan."),
                ):
                    with patch(
                        "backend.app.services.server_service.detect_server_pid",
                        return_value=None,
                    ):
                        payload = load_server_status(local_qwen_home=home)

        self.assertEqual(payload["status"], "active")
        self.assertTrue(payload["hasWarning"])
        self.assertEqual(payload["warningSeverity"], "warning")
        self.assertIn("Health endpoint nije dostupan", payload["warningSummary"])

    def test_start_server_uses_windows_launcher_with_profile_and_wait(self):
        from backend.app.services.server_service import start_server

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            (home / "state" / "settings.json").write_text(
                json.dumps({"profile": "balanced"}),
                encoding="utf-8",
            )
            (home / "state" / "install-state.json").write_text(
                json.dumps({"profile": "speed"}),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.server_service.get_target_platform",
                return_value="windows",
            ):
                with patch(
                    "backend.app.services.server_service.run_windows_launcher",
                    return_value={"status": "ok", "action": "start-server.ps1", "summary": "started"},
                ) as runner:
                    result = start_server(local_qwen_home=home)

        self.assertEqual(result["status"], "ok")
        runner.assert_called_once_with(
            "start-server.ps1",
            "-Profile",
            "balanced",
            "-WaitSeconds",
            "90",
        )

    def test_stop_server_uses_platform_launcher(self):
        from backend.app.services.server_service import stop_server

        with patch(
            "backend.app.services.server_service.run_launcher_by_platform",
            return_value={"status": "ok", "action": "stop-server.ps1", "summary": "stopped"},
        ) as runner:
            result = stop_server()

        self.assertEqual(result["status"], "ok")
        runner.assert_called_once_with("stop-server.sh", "stop-server.ps1")

    def test_open_web_returns_unsupported_on_linux(self):
        from backend.app.services.server_service import open_server_web

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            (home / "state" / "install-state.json").write_text(
                json.dumps({"port": 8091}),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.server_service.get_target_platform",
                return_value="linux",
            ):
                result = open_server_web(local_qwen_home=home)

        self.assertEqual(result["status"], "unsupported")
        self.assertIn("nije izdvojen kao poseban stabilan tok", result["summary"])

    def test_detect_server_pid_matches_requested_port_on_windows(self):
        from backend.app.services.server_service import detect_server_pid

        with patch(
            "backend.app.services.server_service.get_target_platform",
            return_value="windows",
        ):
            with patch("backend.app.services.server_service.subprocess.run") as run_mock:
                run_mock.return_value.returncode = 0
                run_mock.return_value.stdout = "4321\r\n"
                run_mock.return_value.stderr = ""

                pid = detect_server_pid(8091)

        self.assertEqual(pid, 4321)
        command = run_mock.call_args.args[0]
        self.assertIn("--port 8091", command[-1])

    def test_open_web_success_on_windows_returns_opened_url(self):
        from backend.app.services.server_service import open_server_web

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            (home / "state" / "install-state.json").write_text(
                json.dumps({"port": 8091}),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.server_service.get_target_platform",
                return_value="windows",
            ):
                with patch("backend.app.services.server_service.subprocess.run") as run_mock:
                    run_mock.return_value.returncode = 0
                    run_mock.return_value.stdout = ""
                    run_mock.return_value.stderr = ""

                    result = open_server_web(local_qwen_home=home)

        self.assertEqual(result["status"], "ok")
        self.assertIn("http://127.0.0.1:8091/", result["summary"])


if __name__ == "__main__":
    unittest.main()
