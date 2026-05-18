import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BrowserCatalogServiceTests(unittest.TestCase):
    def test_load_catalog_payload_prefers_cache_and_summarizes_refresh_metadata(self):
        from backend.app.services import browser_catalog_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            state_dir = home / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "browser-catalog-cache.json").write_text(
                """
{
  "models": [
    {
      "id": "hf/Qwen3-0.6B-Q8_0.gguf",
      "source": "huggingface",
      "repoId": "Qwen/Qwen3-0.6B-GGUF",
      "filename": "Qwen3-0.6B-Q8_0.gguf",
      "fit": {"status": "nije provereno"}
    },
    {
      "id": "unsloth/Qwen3.6-27B-GGUF/Qwen3.6-27B-UD-IQ3_XXS.gguf",
      "source": "unsloth",
      "repoId": "unsloth/Qwen3.6-27B-GGUF",
      "filename": "Qwen3.6-27B-UD-IQ3_XXS.gguf",
      "fit": {"status": "radi"}
    }
  ],
  "refresh": {
    "lastRefresh": "2026-05-17T18:00:00Z",
    "sources": {
      "huggingface": {
        "lastRefresh": "2026-05-17T18:00:00Z",
        "count": 1,
        "errors": [],
        "warnings": ["repo card missing context window"]
      },
      "unsloth": {
        "lastRefresh": "2026-05-17T18:02:00Z",
        "count": 1,
        "errors": [],
        "warnings": []
      }
    }
  }
}
""".strip(),
                encoding="utf-8",
            )

            payload = browser_catalog_service.load_catalog_payload(local_qwen_home=home)

        self.assertEqual(len(payload["models"]), 2)
        self.assertEqual(payload["refresh"]["counts"]["all"], 2)
        self.assertEqual(payload["refresh"]["counts"]["huggingface"], 1)
        self.assertEqual(payload["refresh"]["counts"]["unsloth"], 1)
        self.assertEqual(payload["refresh"]["warnings"], ["repo card missing context window"])

    def test_refresh_catalog_filters_to_gguf_and_updates_cache(self):
        from backend.app.services import browser_catalog_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            state_dir = home / "state"
            state_dir.mkdir(parents=True)

            def fake_fetch(source: str) -> dict[str, object]:
                self.assertEqual(source, "huggingface")
                return {
                    "models": [
                        {
                            "id": "hf-gguf",
                            "source": "huggingface",
                            "repoId": "Qwen/Qwen3-0.6B-GGUF",
                            "filename": "Qwen3-0.6B-Q8_0.gguf",
                            "sourceUrl": "https://huggingface.co/Qwen/Qwen3-0.6B-GGUF",
                        },
                        {
                            "id": "hf-non-gguf",
                            "source": "huggingface",
                            "repoId": "Qwen/Qwen3-0.6B",
                            "filename": "model.safetensors",
                            "sourceUrl": "https://huggingface.co/Qwen/Qwen3-0.6B",
                        },
                    ],
                    "errors": [],
                    "warnings": ["partial page limit"],
                }

            payload = browser_catalog_service.refresh_catalog(
                source="huggingface",
                local_qwen_home=home,
                fetch_source_catalog=fake_fetch,
                now_iso="2026-05-17T19:00:00Z",
            )

            cache_text = (state_dir / "browser-catalog-cache.json").read_text(encoding="utf-8")

        self.assertEqual([item["id"] for item in payload["models"]], ["hf-gguf"])
        self.assertEqual(payload["refresh"]["counts"]["huggingface"], 1)
        self.assertIn("partial page limit", payload["refresh"]["warnings"])
        self.assertIn("hf-gguf", cache_text)
        self.assertNotIn("hf-non-gguf", cache_text)

    def test_update_model_fit_status_persists_last_known_fit(self):
        from backend.app.services import browser_catalog_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            state_dir = home / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "browser-catalog-cache.json").write_text(
                """
{
  "models": [
    {
      "id": "hf/Qwen3-0.6B-Q8_0.gguf",
      "source": "huggingface",
      "repoId": "Qwen/Qwen3-0.6B-GGUF",
      "filename": "Qwen3-0.6B-Q8_0.gguf",
      "fit": {"status": "nije provereno"}
    }
  ],
  "refresh": {"lastRefresh": "", "sources": {}}
}
""".strip(),
                encoding="utf-8",
            )

            browser_catalog_service.update_model_fit_status(
                "hf/Qwen3-0.6B-Q8_0.gguf",
                {"status": "radi", "checkedAt": "2026-05-17T19:30:00Z", "summary": "staje u masinu"},
                local_qwen_home=home,
            )
            payload = browser_catalog_service.load_catalog_payload(local_qwen_home=home)

        self.assertEqual(payload["models"][0]["fit"]["status"], "radi")
        self.assertEqual(payload["models"][0]["fit"]["checkedAt"], "2026-05-17T19:30:00Z")


if __name__ == "__main__":
    unittest.main()
