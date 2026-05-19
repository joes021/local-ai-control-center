import json
import unittest
from unittest.mock import MagicMock, patch


class UpdatesServiceTests(unittest.TestCase):
    def test_fallback_release_info_uses_public_local_ai_control_center_repo(self):
        from backend.app.services.updates_service import _load_release_info_fallback

        mocked_response = MagicMock()
        mocked_response.__enter__.return_value.read.return_value = json.dumps(
            {
                "tag_name": "v2.24.12",
                "html_url": "https://github.com/joes021/local-ai-control-center/releases/tag/v2.24.12",
                "assets": [
                    {
                        "name": "Local-AI-Control-Center-Setup-2.24.12.exe",
                        "browser_download_url": "https://github.com/joes021/local-ai-control-center/releases/download/v2.24.12/Local-AI-Control-Center-Setup-2.24.12.exe",
                    },
                    {
                        "name": "Local-AI-Control-Center-Setup-linux-x86_64-2.24.12.run",
                        "browser_download_url": "https://github.com/joes021/local-ai-control-center/releases/download/v2.24.12/Local-AI-Control-Center-Setup-linux-x86_64-2.24.12.run",
                    },
                    {
                        "name": "Local-AI-Control-Center-Setup-linux-arm64-2.24.12.run",
                        "browser_download_url": "https://github.com/joes021/local-ai-control-center/releases/download/v2.24.12/Local-AI-Control-Center-Setup-linux-arm64-2.24.12.run",
                    },
                ],
            }
        ).encode("utf-8")

        with patch(
            "backend.app.services.updates_service._read_current_version",
            return_value="2.24.11",
        ), patch(
            "backend.app.services.updates_service.urlopen",
            return_value=mocked_response,
        ):
            payload = _load_release_info_fallback()

        self.assertEqual(payload["latestVersion"], "2.24.12")
        self.assertEqual(payload["releaseUrl"], "https://github.com/joes021/local-ai-control-center/releases/tag/v2.24.12")
        self.assertTrue(payload["windowsInstallerUrl"].endswith(".exe"))
        self.assertIn("linux-x86_64", payload["linuxX64InstallerUrl"])
        self.assertIn("linux-arm64", payload["linuxArm64InstallerUrl"])


if __name__ == "__main__":
    unittest.main()
