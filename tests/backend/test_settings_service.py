import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class SettingsServiceTests(unittest.TestCase):
    def test_turboquant_schema_exposes_builtin_presets_and_recommended_models(self):
        from backend.app.services.settings_service import load_turboquant_schema

        payload = load_turboquant_schema()

        self.assertIn("parameters", payload)
        self.assertIn("builtInPresets", payload)
        self.assertIn("recommendedModels", payload)
        self.assertTrue(any(item["id"] == "safe" for item in payload["builtInPresets"]))
        self.assertTrue(any(item["id"] == "daily" for item in payload["builtInPresets"]))
        self.assertTrue(any(item["id"] == "max-context" for item in payload["builtInPresets"]))
        self.assertTrue(
            any(
                item["id"] == "unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf"
                for item in payload["recommendedModels"]
            )
        )

    def test_turboquant_user_preset_roundtrip_preserves_settings(self):
        from backend.app.services.settings_service import (
            delete_turboquant_user_preset,
            load_turboquant_schema,
            save_turboquant_user_preset,
        )

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)

            saved = save_turboquant_user_preset(
                {
                    "name": "Moj 3060 daily",
                    "description": "Balans za dnevni rad.",
                    "targetModelPattern": "qwen36-35b*",
                    "notes": "Test preset",
                    "settings": {
                        "context": 131072,
                        "ctk": "turbo4",
                        "ctv": "turbo3",
                        "ncmoe": 20,
                        "flashAttention": True,
                        "mlock": True,
                        "mmapMode": "no-mmap",
                        "runtimePreference": "turboquant",
                    },
                },
                local_qwen_home=home,
            )

            payload = load_turboquant_schema(local_qwen_home=home)
            restored = next(
                item for item in payload["userPresets"] if item["id"] == saved["id"]
            )

            self.assertEqual(restored["name"], "Moj 3060 daily")
            self.assertEqual(restored["settings"]["ctk"], "turbo4")
            self.assertEqual(restored["settings"]["runtimePreference"], "turboquant")

            deleted = delete_turboquant_user_preset(saved["id"], local_qwen_home=home)
            self.assertTrue(deleted)

    def test_thinking_mode_maps_to_step_values(self):
        from backend.app.services.settings_service import apply_thinking_mode

        cfg = apply_thinking_mode("high")

        self.assertGreater(cfg["buildSteps"], 0)
        self.assertGreater(cfg["planSteps"], 0)
        self.assertGreater(cfg["generalSteps"], 0)
        self.assertGreater(cfg["exploreSteps"], 0)
        self.assertEqual(cfg["thinkingMode"], "high")

    def test_model_override_roundtrip_preserves_scope_and_target_model(self):
        from backend.app.services.settings_service import (
            load_model_override_payload,
            save_model_override_payload,
        )

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            state_dir = home / "state"
            state_dir.mkdir(parents=True)

            payload = {
                "modelId": "qwen36-35b-a3b-IQ2_M.gguf",
                "profile": "balanced",
                "context": 131072,
                "outputTokens": 8192,
                "workingDirectory": "/home/demo",
                "thinkingMode": "low",
            }
            save_model_override_payload(payload, local_qwen_home=home)
            restored = load_model_override_payload(
                "qwen36-35b-a3b-IQ2_M.gguf", local_qwen_home=home
            )

            self.assertEqual(restored["modelId"], "qwen36-35b-a3b-IQ2_M.gguf")
            self.assertEqual(restored["thinkingMode"], "low")
            self.assertEqual(restored["workingDirectory"], "/home/demo")

    def test_global_defaults_roundtrip_preserves_baseline(self):
        from backend.app.services.settings_service import (
            load_global_defaults_payload,
            save_global_defaults_payload,
        )

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            payload = {
                "profile": "balanced",
                "context": 262144,
                "outputTokens": 8192,
                "workingDirectory": "/home/demo",
                "thinkingMode": "mid",
            }
            save_global_defaults_payload(payload, local_qwen_home=home)
            restored = load_global_defaults_payload(local_qwen_home=home)

            self.assertIsNotNone(restored)
            self.assertEqual(restored["thinkingMode"], "mid")
            self.assertEqual(restored["workingDirectory"], "/home/demo")

    def test_runtime_config_roundtrip_preserves_access_mode(self):
        from backend.app.services.runtime_config_service import (
            load_runtime_config,
            save_runtime_config,
        )

        with TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            save_runtime_config({"accessMode": "tailscale"}, state_dir=state_dir)
            restored = load_runtime_config(state_dir=state_dir)

            self.assertEqual(restored["accessMode"], "tailscale")

    def test_opencode_step_preset_roundtrip_preserves_values(self):
        from backend.app.services.settings_service import (
            delete_opencode_step_preset,
            load_opencode_step_schema,
            save_opencode_step_preset,
        )

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)

            saved = save_opencode_step_preset(
                {
                    "name": "Moj coding daily",
                    "steps": {
                        "buildSteps": 150,
                        "planSteps": 105,
                        "generalSteps": 115,
                        "exploreSteps": 82,
                    },
                },
                local_qwen_home=home,
            )

            payload = load_opencode_step_schema(
                current_steps={
                    "buildSteps": 80,
                    "planSteps": 60,
                    "generalSteps": 70,
                    "exploreSteps": 40,
                },
                local_qwen_home=home,
            )
            restored = next(item for item in payload["userPresets"] if item["id"] == saved["id"])

            self.assertEqual(restored["name"], "Moj coding daily")
            self.assertEqual(restored["steps"]["buildSteps"], 150)
            self.assertEqual(restored["steps"]["exploreSteps"], 82)

            deleted = delete_opencode_step_preset(saved["id"], local_qwen_home=home)
            self.assertTrue(deleted)

    def test_opencode_step_schema_exposes_builtin_presets(self):
        from backend.app.services.settings_service import load_opencode_step_schema

        payload = load_opencode_step_schema(
            current_steps={
                "buildSteps": 140,
                "planSteps": 100,
                "generalSteps": 110,
                "exploreSteps": 80,
            }
        )

        names = [item["name"] for item in payload["builtInPresets"]]
        self.assertIn("Safe", names)
        self.assertIn("Daily", names)
        self.assertIn("Deep", names)
        self.assertIn("Max", names)


if __name__ == "__main__":
    unittest.main()
