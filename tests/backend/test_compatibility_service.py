import unittest


class CompatibilityServiceTests(unittest.TestCase):
    def test_calculate_fit_returns_radi_when_system_meets_requirements(self):
        from backend.app.services.compatibility_service import calculate_compatibility

        result = calculate_compatibility(
            {
                "id": "hf/small",
                "family": "Qwen",
                "quantization": "Q4_K_M",
                "approxSizeGiB": 4.0,
                "minimumRamGiB": 8,
                "minimumVramGiB": 6,
                "recommendedVramGiB": 8,
                "contextWindow": 8192,
                "defaultOutputTokens": 2048,
                "moe": False,
                "turboQuantReady": False,
            },
            system_info={"ramGiB": 32, "vramGiB": 12, "turboQuantAvailable": False},
        )

        self.assertEqual(result["status"], "radi")
        self.assertIn("dovoljno", result["reasoning"]["vram"])
        self.assertEqual(result["fitLabel"], "Radi")
        self.assertIn("speedLabel", result)
        self.assertIn("memoryBudget", result)
        self.assertIn("recommendations", result)

    def test_calculate_fit_returns_granicno_when_turboquant_effect_is_needed(self):
        from backend.app.services.compatibility_service import calculate_compatibility

        result = calculate_compatibility(
            {
                "id": "unsloth/medium",
                "family": "Qwen",
                "quantization": "IQ3_XXS",
                "approxSizeGiB": 10.5,
                "minimumRamGiB": 16,
                "minimumVramGiB": 11,
                "recommendedVramGiB": 14,
                "contextWindow": 32768,
                "defaultOutputTokens": 4096,
                "moe": True,
                "turboQuantReady": True,
            },
            system_info={"ramGiB": 32, "vramGiB": 12, "turboQuantAvailable": True},
        )

        self.assertEqual(result["status"], "granicno")
        self.assertIn("TurboQuant", result["reasoning"]["turboQuantEffect"])
        self.assertIn("MoE", result["reasoning"]["moeEffect"])
        self.assertTrue(result["recommendations"])
        self.assertEqual(result["speedLabel"], "Sporije")

    def test_calculate_fit_returns_ne_radi_when_system_is_too_small(self):
        from backend.app.services.compatibility_service import calculate_compatibility

        result = calculate_compatibility(
            {
                "id": "hf/large",
                "family": "Qwen",
                "quantization": "Q8_0",
                "approxSizeGiB": 28.0,
                "minimumRamGiB": 48,
                "minimumVramGiB": 24,
                "recommendedVramGiB": 32,
                "contextWindow": 32768,
                "defaultOutputTokens": 4096,
                "moe": False,
                "turboQuantReady": False,
            },
            system_info={"ramGiB": 16, "vramGiB": 8, "turboQuantAvailable": False},
        )

        self.assertEqual(result["status"], "ne radi")
        self.assertIn("premalo", result["reasoning"]["ram"])
        self.assertEqual(result["fitLabel"], "Ne radi")
        self.assertEqual(result["memoryBudget"]["contextPressure"]["level"], "high")

    def test_calculate_fit_returns_nije_provereno_when_system_info_is_missing(self):
        from backend.app.services.compatibility_service import calculate_compatibility

        result = calculate_compatibility(
            {
                "id": "hf/unknown",
                "family": "Qwen",
                "quantization": "Q4_K_M",
            },
            system_info={"ramGiB": None, "vramGiB": None, "turboQuantAvailable": False},
        )

        self.assertEqual(result["status"], "nije provereno")
        self.assertIn("Nije bilo dovoljno", result["summary"])
        self.assertEqual(result["fitLabel"], "Nije provereno")

    def test_calculate_fit_includes_applyable_recommendations_for_context_output_and_turboquant(self):
        from backend.app.services.compatibility_service import calculate_compatibility

        result = calculate_compatibility(
            {
                "id": "unsloth/qwen35b",
                "family": "Qwen",
                "quantization": "IQ3_S",
                "approxSizeGiB": 10.7,
                "minimumRamGiB": 20,
                "minimumVramGiB": 10.5,
                "recommendedVramGiB": 13.5,
                "contextWindow": 262144,
                "defaultOutputTokens": 8192,
                "moe": True,
                "turboQuantReady": True,
            },
            system_info={
                "ramGiB": 32,
                "vramGiB": 12,
                "turboQuantAvailable": True,
                "context": 262144,
                "outputTokens": 8192,
                "turboQuantConfig": {
                    "ctk": "turbo4",
                    "ctv": "turbo4",
                    "ncmoe": 20,
                    "runtimePreference": "llama.cpp",
                },
            },
        )

        action_kinds = [item.get("action", {}).get("kind") for item in result["recommendations"]]
        self.assertIn("set-context", action_kinds)
        self.assertIn("set-output", action_kinds)
        self.assertIn("set-runtime-preference", action_kinds)


if __name__ == "__main__":
    unittest.main()
