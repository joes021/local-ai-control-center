import unittest
from unittest import mock


class PlatformServicesTests(unittest.TestCase):
    def test_platform_config_defaults_to_host_windows(self):
        from backend.app.services import platform_config

        with (
            mock.patch.dict("os.environ", {}, clear=True),
            mock.patch.object(platform_config.sys, "platform", "win32"),
        ):
            self.assertEqual(platform_config.get_target_platform(), "windows")

    def test_logs_service_uses_platform_launcher(self):
        from backend.app.services import logs_service

        windows_payload = {"status": "ok", "action": "show-logs.ps1", "summary": "windows"}

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(
                logs_service,
                "run_launcher_by_platform",
                return_value=windows_payload,
            ) as runner,
        ):
            result = logs_service.load_logs_preview()

        self.assertEqual(result, windows_payload)
        runner.assert_called_once_with("show-logs.sh", "show-logs.ps1")

    def test_repair_service_uses_platform_launcher(self):
        from backend.app.services import repair_service

        windows_payload = {"status": "ok", "action": "repair-install.ps1", "summary": "windows"}

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(
                repair_service,
                "run_launcher_by_platform",
                return_value=windows_payload,
            ) as runner,
        ):
            result = repair_service.run_repair_install()

        self.assertEqual(result, windows_payload)
        runner.assert_called_once_with(
            "repair-install.sh", "repair-install.ps1"
        )

    def test_updates_service_uses_platform_launcher(self):
        from backend.app.services import updates_service

        windows_payload = {"status": "ok", "action": "check-updates.ps1", "summary": "windows"}

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(
                updates_service,
                "run_launcher_by_platform",
                return_value=windows_payload,
            ) as runner,
        ):
            result = updates_service.check_updates()

        self.assertEqual(result, windows_payload)
        runner.assert_called_once_with(
            "check-updates.sh", "check-updates.ps1"
        )


if __name__ == "__main__":
    unittest.main()
