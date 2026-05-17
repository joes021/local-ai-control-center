import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class ModelsServiceTests(unittest.TestCase):
    def test_models_payload_groups_curated_local_hf_and_unsloth_models(self):
        from backend.app.services.models_service import normalize_models

        payload = normalize_models(
            [
                {"id": "qwen36-35b-a3b-IQ2_M.gguf", "source": "curated", "active": True},
                {"id": "local-demo.gguf", "source": "local", "active": False},
                {"id": "hf-Qwen3-0.6B-Q8_0.gguf", "source": "huggingface", "active": False},
                {"id": "unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf", "source": "unsloth", "active": False},
            ]
        )

        self.assertEqual(len(payload["curated"]), 1)
        self.assertEqual(len(payload["local"]), 1)
        self.assertEqual(len(payload["huggingFace"]), 1)
        self.assertEqual(len(payload["unsloth"]), 1)
        self.assertTrue(payload["curated"][0]["active"])

    def test_delete_custom_model_removes_registry_entry_and_file(self):
        from backend.app.services.models_service import delete_model

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            models_dir = home / "models"
            state_dir = home / "state"
            models_dir.mkdir()
            state_dir.mkdir()

            target = models_dir / "demo.gguf"
            target.write_bytes(b"demo")
            registry = state_dir / "custom-models.json"
            registry.write_text(
                """
{
  "models": [
    {
      "id": "local-demo.gguf",
      "filename": "demo.gguf",
      "customSource": "local-file"
    }
  ]
}
""".strip(),
                encoding="utf-8",
            )

            result = delete_model(
                "local-demo.gguf",
                local_qwen_home=home,
                remove_file=True,
                remove_registry=True,
            )

            self.assertEqual(result["status"], "ok")
            self.assertFalse(target.exists())
            self.assertNotIn("local-demo.gguf", registry.read_text(encoding="utf-8"))

    def test_delete_requires_at_least_one_action(self):
        from backend.app.services.models_service import delete_model

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            models_dir = home / "models"
            state_dir = home / "state"
            models_dir.mkdir()
            state_dir.mkdir()
            (home / "config" / "profiles").mkdir(parents=True)
            (home / "config" / "profiles" / "defaults.json").write_text(
                '{"modelChoices":{"demo":{"id":"demo.gguf","filename":"demo.gguf"}}}',
                encoding="utf-8",
            )

            result = delete_model(
                "demo.gguf",
                local_qwen_home=home,
                remove_file=False,
                remove_registry=False,
            )

            self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
