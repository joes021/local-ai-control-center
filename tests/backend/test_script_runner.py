import unittest
from pathlib import Path
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

    def test_target_architecture_normalizes_arm64_variants(self):
        from backend.app.services import platform_config

        with mock.patch.object(platform_config.platform, "machine", return_value="aarch64"):
            self.assertEqual(platform_config.detect_host_architecture(), "arm64")

    def test_resolve_linux_launcher_path_uses_repo_launcher_when_installed_copy_missing(self):
        from backend.app.services import script_runner

        fake_repo_root = Path("/tmp/local-ai-control-center")
        with (
            mock.patch.object(script_runner, "detect_local_qwen_home", return_value=Path("/tmp/local-qwen-home")),
            mock.patch.object(script_runner, "detect_control_center_repo_root", return_value=fake_repo_root),
        ):
            resolved = script_runner.resolve_linux_launcher_path("start-control-center-next.sh")

        self.assertEqual(
            resolved,
            fake_repo_root / "launchers" / "linux" / "start-control-center-next.sh",
        )


if __name__ == "__main__":
    unittest.main()
