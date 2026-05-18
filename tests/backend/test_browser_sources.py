import unittest


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


if __name__ == "__main__":
    unittest.main()
