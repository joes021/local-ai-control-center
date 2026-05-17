import unittest
from unittest import mock


class NativeDialogsTests(unittest.TestCase):
    def test_choose_dialog_command_prefers_zenity(self):
        from backend.app.services.native_dialogs import choose_dialog_command

        picked = choose_dialog_command(
            which_command=lambda name: "/usr/bin/zenity" if name == "zenity" else None
        )

        self.assertEqual(picked, "zenity")

    def test_pick_file_uses_windows_dialog_when_target_platform_is_windows(self):
        from backend.app.services import native_dialogs

        completed = mock.Mock(returncode=0, stdout="C:\\demo\\model.gguf\n", stderr="")

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(native_dialogs.subprocess, "run", return_value=completed) as run_mock,
        ):
            result = native_dialogs.pick_file(
                title="Izaberi lokalni GGUF model",
                file_filter_name="GGUF",
                pattern="*.gguf",
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["path"], "C:\\demo\\model.gguf")
        self.assertEqual(run_mock.call_args.args[0][0], "powershell")

    def test_pick_directory_uses_windows_dialog_when_target_platform_is_windows(self):
        from backend.app.services import native_dialogs

        completed = mock.Mock(returncode=0, stdout="C:\\Users\\AzdahaI9\\Documents\n", stderr="")

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(native_dialogs.subprocess, "run", return_value=completed) as run_mock,
        ):
            result = native_dialogs.pick_directory(title="Izaberi working directory")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["path"], "C:\\Users\\AzdahaI9\\Documents")
        self.assertEqual(run_mock.call_args.args[0][0], "powershell")


if __name__ == "__main__":
    unittest.main()
