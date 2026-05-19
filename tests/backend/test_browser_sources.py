import unittest
from unittest.mock import patch


class BrowserSourcesTests(unittest.TestCase):
    def test_normalize_model_entry_exposes_size_bytes_and_label(self):
        from backend.app.services import browser_sources

        item = browser_sources._normalize_model_entry(
            source="unsloth",
            repo_id="unsloth/gemma-4-E4B-it-GGUF",
            repo={
                "createdAt": "2026-05-18T10:00:00Z",
                "lastModified": "2026-05-19T10:00:00Z",
            },
            sibling={
                "rfilename": "gemma-4-E4B-it-Q4_0.gguf",
                "size": 3 * 1024 * 1024 * 1024,
            },
            filename="gemma-4-E4B-it-Q4_0.gguf",
        )

        self.assertEqual(item["filename"], "gemma-4-E4B-it-Q4_0.gguf")
        self.assertEqual(item["sizeBytes"], 3 * 1024 * 1024 * 1024)
        self.assertEqual(item["sizeLabel"], "3.0 GiB")
        self.assertEqual(item["sourceUrl"], "https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF")

    def test_fetch_hf_models_uses_tree_sizes_when_siblings_do_not_expose_size(self):
        from backend.app.services import browser_sources

        repo_payload = [
            {
                "id": "unsloth/Qwen3.6-27B-MTP-GGUF",
                "createdAt": "2026-05-18T10:00:00Z",
                "lastModified": "2026-05-19T10:00:00Z",
                "siblings": [
                    {"rfilename": "Qwen3.6-27B-IQ4_XS.gguf"},
                ],
            }
        ]
        tree_payload = [
            {"path": "Qwen3.6-27B-IQ4_XS.gguf", "size": 7 * 1024 * 1024 * 1024},
        ]

        with patch(
            "backend.app.services.browser_sources._read_json",
            side_effect=[repo_payload, tree_payload],
        ):
            result = browser_sources.fetch_unsloth_catalog(limit=1)

        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.models), 1)
        self.assertEqual(result.models[0]["sizeBytes"], 7 * 1024 * 1024 * 1024)
        self.assertEqual(result.models[0]["sizeLabel"], "7.0 GiB")

    def test_read_repo_file_sizes_preserves_repo_slash_in_tree_url(self):
        from backend.app.services import browser_sources

        def fake_read_json(url: str):
            self.assertIn("/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=1", url)
            return [{"path": "demo.gguf", "size": 123}]

        with patch("backend.app.services.browser_sources._read_json", side_effect=fake_read_json):
            payload = browser_sources._read_repo_file_sizes("unsloth/Qwen3.6-35B-A3B-GGUF")

        self.assertEqual(payload, {"demo.gguf": 123})


if __name__ == "__main__":
    unittest.main()
