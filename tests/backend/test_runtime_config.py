import os
import unittest
from unittest.mock import patch


class RuntimeConfigTests(unittest.TestCase):
    def test_backend_config_reads_ui_port_from_environment(self):
        from backend.app.config import get_config

        with patch.dict(os.environ, {"CONTROL_CENTER_NEXT_UI_PORT": "3214"}, clear=False):
            cfg = get_config()

        self.assertEqual(cfg.ui_port, 3214)
        self.assertEqual(cfg.access_mode, "local-only")

    def test_backend_config_reads_access_mode_from_environment(self):
        from backend.app.config import get_config

        with patch.dict(
            os.environ,
            {"CONTROL_CENTER_NEXT_ACCESS_MODE": "tailscale", "CONTROL_CENTER_NEXT_HOST": "0.0.0.0"},
            clear=False,
        ):
            cfg = get_config()

        self.assertEqual(cfg.access_mode, "tailscale")
        self.assertEqual(cfg.host, "0.0.0.0")


if __name__ == "__main__":
    unittest.main()
