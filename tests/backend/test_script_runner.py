import unittest
from unittest import mock


class ScriptRunnerTests(unittest.TestCase):
    def test_build_result_payload_marks_success(self):
        from backend.app.services.script_runner import build_result_payload

        payload = build_result_payload(
            returncode=0,
            stdout="Sve je u redu",
            stderr="",
            action="repair-install",
        )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"], "Sve je u redu")
        self.assertEqual(payload["action"], "repair-install")

    def test_target_platform_defaults_to_host_platform(self):
        from backend.app.services import platform_config

        with (
            mock.patch.dict("os.environ", {}, clear=True),
            mock.patch.object(platform_config.sys, "platform", "win32"),
        ):
            self.assertEqual(platform_config.get_target_platform(), "windows")

    def test_target_platform_accepts_windows(self):
        from backend.app.services.platform_config import get_target_platform

        with mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False):
            self.assertEqual(get_target_platform(), "windows")


if __name__ == "__main__":
    unittest.main()
