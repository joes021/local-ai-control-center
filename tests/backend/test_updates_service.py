import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


class UpdatesServiceTests(unittest.TestCase):
    def test_read_update_progress_returns_idle_when_missing(self):
        from backend.app.services import updates_service

        with TemporaryDirectory() as tmp:
            with mock.patch.object(
                updates_service,
                "load_update_release_info",
                return_value={
                    "currentVersion": "2.10.2",
                    "latestVersion": "2.10.57",
                    "releaseUrl": "https://example.test/release",
                },
            ):
                payload = updates_service.read_update_progress(Path(tmp))

        self.assertEqual(payload["status"], "idle")
        self.assertFalse(payload["isActive"])
        self.assertIn("Nema aktivnog update", payload["message"])
        self.assertEqual(payload["currentVersion"], "2.10.2")
        self.assertEqual(payload["latestVersion"], "2.10.57")

    def test_start_install_update_job_returns_accepted_and_writes_progress_file(self):
        from backend.app.services import updates_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)

            fake_info = {
                "currentVersion": "2.10.2",
                "latestVersion": "2.10.3",
                "updateAvailable": True,
                "releaseUrl": "https://example.test/release",
                "windowsInstallerUrl": "https://example.test/Local-Qwen-Setup-latest.exe",
                "linuxInstallerUrl": "https://example.test/Local-Qwen-Setup-latest.run",
            }

            with (
                mock.patch.dict(
                    "os.environ",
                    {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"},
                    clear=False,
                ),
                mock.patch.object(
                    updates_service, "load_update_release_info", return_value=fake_info
                ),
                mock.patch.object(
                    updates_service, "_spawn_install_update_job", return_value="update-job-123"
                ),
            ):
                payload = updates_service.start_install_update_job(local_qwen_home=home)

            self.assertEqual(payload["status"], "accepted")
            self.assertEqual(payload["action"], "install-update")
            self.assertTrue(str(payload["actionId"]).startswith("update-"))

            progress_path = home / "state" / "update-progress.json"
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            self.assertEqual(progress["status"], "accepted")
            self.assertEqual(progress["latestVersion"], "2.10.3")
            self.assertIn("installer ce se automatski pokrenuti", progress["message"].lower())

    def test_windows_target_path_is_versioned_instead_of_reusing_latest_filename(self):
        from backend.app.services import updates_service

        with mock.patch.dict(
            "os.environ",
            {"TEMP": r"C:\Temp", "CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"},
            clear=False,
        ):
            path = updates_service._resolve_target_path(Path(r"C:\Dummy"), "2.10.57", "windows")

        self.assertIn("2.10.57", path.name)
        self.assertTrue(path.name.endswith(".exe"))
        self.assertNotEqual(path.name, "Local-Qwen-Setup-latest.exe")

    def test_read_update_progress_normalizes_legacy_access_denied_error(self):
        from backend.app.services import updates_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            state_dir = home / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "update-progress.json").write_text(
                json.dumps(
                    {
                        "actionId": "update-old",
                        "status": "error",
                        "phase": "error",
                        "isActive": False,
                        "message": "[WinError 5] Access is denied: 'C:\\\\Users\\\\Demo\\\\AppData\\\\Local\\\\Temp\\\\LocalQwenUpdate\\\\Local-Qwen-Setup-latest.exe'",
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(
                updates_service,
                "load_update_release_info",
                return_value={
                    "currentVersion": "2.10.2",
                    "latestVersion": "2.10.57",
                    "releaseUrl": "https://example.test/release",
                },
            ):
                payload = updates_service.read_update_progress(home)

        self.assertEqual(payload["currentVersion"], "2.10.2")
        self.assertEqual(payload["latestVersion"], "2.10.57")
        self.assertIn("Najverovatnije je prethodni installer jos otvoren", payload["message"])
        self.assertIn("Local-Qwen-Setup-latest.exe", payload["targetPath"])


if __name__ == "__main__":
    unittest.main()
