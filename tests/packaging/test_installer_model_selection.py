import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODELS_PATH = ROOT / "install" / "shared" / "recommended-models.json"

EXPECTED_RECOMMENDED_MODELS = [
    {
        "modelId": "gemma-4-e4b-it-q4-0",
        "downloadFile": "gemma-4-E4B-it-Q4_0.gguf",
        "vramGiB": 6,
    },
    {
        "modelId": "qwen3.6-35b-a3b-ud-iq2-xxs",
        "downloadFile": "Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf",
        "vramGiB": 12,
    },
    {
        "modelId": "qwen3.6-35b-a3b-mtp-ud-q4-k-xl",
        "downloadFile": "Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_XL",
        "vramGiB": 24,
    },
]


class InstallerModelSelectionTests(unittest.TestCase):
    def test_shared_recommended_models_payload_has_expected_shape(self):
        payload = json.loads(MODELS_PATH.read_text(encoding="utf-8"))

        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("schemaVersion"), 1)
        self.assertEqual(payload.get("defaultModelId"), "gemma-4-e4b-it-q4-0")
        self.assertIn("recommended", payload)
        self.assertIsInstance(payload["recommended"], list)
        self.assertNotIn("extra", payload)
        self.assertEqual(len(payload["recommended"]), 3)

        actual_models = [
            {
                "modelId": entry["modelId"],
                "downloadFile": entry["downloadFile"],
                "vramGiB": entry["vramClass"]["recommendedGiB"],
            }
            for entry in payload["recommended"]
        ]
        self.assertEqual(actual_models, EXPECTED_RECOMMENDED_MODELS)

        for entry in payload["recommended"]:
            self.assertIsInstance(entry, dict)
            for key in ("modelId", "label", "description", "downloadFile", "vramClass"):
                self.assertIn(key, entry)
            self.assertIsInstance(entry["modelId"], str)
            self.assertIsInstance(entry["label"], str)
            self.assertIsInstance(entry["description"], str)
            self.assertIsInstance(entry["downloadFile"], str)
            self.assertIsInstance(entry["vramClass"], dict)
            for key in ("label", "minimumGiB", "recommendedGiB"):
                self.assertIn(key, entry["vramClass"])
            self.assertEqual(entry["vramClass"]["minimumGiB"], entry["vramClass"]["recommendedGiB"])


if __name__ == "__main__":
    unittest.main()
