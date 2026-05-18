import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


class OpenCodeServiceTests(unittest.TestCase):
    def test_load_opencode_status_payload_uses_windows_common_and_agent_meta(self):
        from backend.app.services import opencode_service

        responses = {
            "Test-OpenCodeAvailable": {"status": "ok", "payload": True},
            "Get-OpenCodeConfigPath": {"status": "ok", "payload": r"C:\Users\demo\.config\opencode\opencode.json"},
            "Get-OpenCodeExecutable": {"status": "ok", "payload": r"C:\Users\demo\AppData\Roaming\npm\opencode.cmd"},
        }

        with (
            TemporaryDirectory() as tmp,
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(opencode_service, "load_settings_payload", return_value={
                "profile": "balanced",
                "workingDirectory": r"C:\work",
                "buildSteps": 80,
                "planSteps": 60,
                "generalSteps": 70,
                "exploreSteps": 40,
            }),
            mock.patch.object(opencode_service, "invoke_windows_common_json", side_effect=lambda name, *args: responses[name]),
        ):
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            (home / "state" / "agent-launch-settings.json").write_text(
                """
{
  "securityMode": "blacklist",
  "capabilityMode": "confirm-commands",
  "workingFolder": "C:\\\\repo",
  "profile": "video",
  "audit": {
    "riskLevel": "medium",
    "reasons": ["Van workspace foldera trazi potvrdu."]
  }
}
""".strip(),
                encoding="utf-8",
            )
            with (
                mock.patch.object(opencode_service, "detect_local_qwen_home", return_value=home),
                mock.patch.object(
                    opencode_service,
                    "_detect_opencode_instances",
                    return_value=[
                        {
                            "pid": 4321,
                            "name": "node.exe",
                            "commandLine": r"C:\Program Files\nodejs\node.exe opencode",
                        }
                    ],
                ),
            ):
                payload = opencode_service.load_opencode_status_payload()

        self.assertTrue(payload["available"])
        self.assertTrue(payload["active"])
        self.assertEqual(payload["instanceCount"], 1)
        self.assertEqual(payload["instances"][0]["pid"], 4321)
        self.assertEqual(payload["workingDirectory"], r"C:\repo")
        self.assertEqual(payload["securityMode"], "workspace-write")
        self.assertEqual(payload["securityModeLabel"], "Ogranicen agent sa blacklist pravilima")
        self.assertEqual(payload["capabilityMode"], "confirm-commands")
        self.assertEqual(payload["capabilityModeLabel"], "3. Citanje + izmena + komande uz potvrdu")
        self.assertEqual(payload["profile"], "video")
        self.assertIn("medium", payload["auditSummary"])

    def test_detect_windows_instances_prefers_real_opencode_processes_over_wrappers(self):
        from backend.app.services import opencode_service

        raw_instances = [
            {"pid": 111, "name": "powershell.exe", "commandLine": "powershell ... opencode"},
            {"pid": 222, "name": "node.exe", "commandLine": "node ... opencode"},
            {"pid": 333, "name": "opencode.exe", "commandLine": r"C:\tool\opencode.exe --model foo"},
            {"pid": 444, "name": "powershell.exe", "commandLine": "powershell ... opencode"},
            {"pid": 555, "name": "node.exe", "commandLine": "node ... opencode"},
            {"pid": 666, "name": "opencode.exe", "commandLine": r"C:\tool\opencode.exe --model foo"},
        ]

        filtered = opencode_service._prefer_primary_opencode_instances(raw_instances)

        self.assertEqual([item["pid"] for item in filtered], [333, 666])

    def test_load_opencode_status_payload_returns_empty_instance_data_when_unavailable(self):
        from backend.app.services import opencode_service

        with mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "linux"}, clear=False):
            with mock.patch.object(
                opencode_service,
                "load_settings_payload",
                return_value={"profile": "balanced", "workingDirectory": "/repo"},
            ):
                with mock.patch.object(
                    opencode_service,
                    "_resolve_linux_opencode_executable",
                    return_value="/usr/local/bin/opencode",
                ):
                    with mock.patch.object(
                        opencode_service,
                        "_detect_opencode_instances",
                        return_value=[
                            {
                                "pid": 2020,
                                "name": "opencode",
                                "commandLine": "/usr/local/bin/opencode",
                            }
                        ],
                    ):
                        payload = opencode_service.load_opencode_status_payload()

        self.assertTrue(payload["available"])
        self.assertTrue(payload["active"])
        self.assertEqual(payload["instanceCount"], 1)
        self.assertEqual(payload["instances"][0]["pid"], 2020)
        self.assertEqual(payload["executablePath"], "/usr/local/bin/opencode")
        self.assertEqual(payload["configPath"], str(Path.home() / ".config" / "opencode" / "opencode.json"))
        self.assertIn("Linux", payload["auditSummary"])

    def test_apply_opencode_settings_reports_success_when_save_and_audit_pass(self):
        from backend.app.services import opencode_service

        completed = mock.Mock(returncode=0, stdout="ok", stderr="")
        with (
            TemporaryDirectory() as tmp,
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(opencode_service, "detect_local_qwen_home", return_value=Path(tmp)),
            mock.patch.object(opencode_service, "_load_windows_settings_json", return_value={"profile": "balanced", "llama": {}, "opencode": {}}),
            mock.patch.object(opencode_service, "_run_powershell_command", return_value=completed),
            mock.patch.object(opencode_service, "_run_powershell_file", return_value=completed),
        ):
            result = opencode_service.apply_opencode_settings(
                {
                    "profile": "balanced",
                    "context": 262144,
                    "outputTokens": 8192,
                    "workingDirectory": r"C:\repo",
                    "buildSteps": 80,
                    "planSteps": 60,
                    "generalSteps": 70,
                    "exploreSteps": 40,
                    "securityMode": "strict",
                    "capabilityMode": "confirm-commands",
                }
            )

        self.assertEqual(result["status"], "ok")
        self.assertIn("OpenCode settings su sacuvani", result["summary"])

    def test_open_opencode_reports_success_when_launcher_returns_zero(self):
        from backend.app.services import opencode_service

        completed = mock.Mock(returncode=0, stdout="OpenCode je pokrenut.", stderr="")
        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(opencode_service, "_run_powershell_file", return_value=completed),
            mock.patch.object(opencode_service, "_resolve_windows_launcher_script", return_value=Path(r"C:\demo\start-opencode.ps1")),
        ):
            result = opencode_service.open_opencode("balanced")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "open-opencode")

    def test_open_opencode_on_linux_uses_launcher_script(self):
        from backend.app.services import opencode_service

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "linux"}, clear=False),
            mock.patch.object(opencode_service, "_resolve_linux_opencode_launcher_script", return_value="/repo/launchers/start-opencode.sh"),
            mock.patch.object(opencode_service.subprocess, "Popen") as popen_mock,
        ):
            result = opencode_service.open_opencode("balanced")

        self.assertEqual(result["status"], "ok")
        command = popen_mock.call_args.args[0]
        self.assertEqual(command[0], "bash")
        self.assertEqual(command[1], "/repo/launchers/start-opencode.sh")
        self.assertEqual(command[2], "balanced")


if __name__ == "__main__":
    unittest.main()
