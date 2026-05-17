import unittest


class NativeDialogsTests(unittest.TestCase):
    def test_choose_dialog_command_prefers_zenity(self):
        from backend.app.services.native_dialogs import choose_dialog_command

        picked = choose_dialog_command(
            which_command=lambda name: "/usr/bin/zenity" if name == "zenity" else None
        )

        self.assertEqual(picked, "zenity")


if __name__ == "__main__":
    unittest.main()
