import unittest


class SettingsApplyTests(unittest.TestCase):
    def test_build_configure_settings_env_maps_payload(self):
        from backend.app.services.settings_service import build_configure_settings_env

        env = build_configure_settings_env(
            {
                "profile": "balanced",
                "context": 262144,
                "outputTokens": 32000,
                "workingDirectory": "/home/joes021",
                "thinkingMode": "high",
            }
        )

        self.assertEqual(env["PROFILE"], "balanced")
        self.assertEqual(env["CONTEXT_SIZE"], "262144")
        self.assertEqual(env["MAX_OUTPUT_TOKENS"], "32000")
        self.assertEqual(env["WORKING_DIRECTORY"], "/home/joes021")
        self.assertEqual(env["BUILD_STEPS"], "120")
        self.assertEqual(env["PLAN_STEPS"], "100")
        self.assertEqual(env["GENERAL_STEPS"], "100")
        self.assertEqual(env["EXPLORE_STEPS"], "60")


if __name__ == "__main__":
    unittest.main()
