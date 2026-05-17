import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class BenchmarkServiceTests(unittest.TestCase):
    def test_load_benchmark_summary_reads_history_and_builds_metrics(self):
        from backend.app.services.benchmark_service import load_benchmark_summary

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            state = home / "state"
            state.mkdir(parents=True, exist_ok=True)
            history_path = state / "token-metrics-history.json"
            (state / "benchmark-batteries.json").write_text(
                json.dumps(
                    {
                        "activeBatteryId": "default",
                        "batteries": [
                            {
                                "id": "default",
                                "name": "Default battery",
                                "source": "default",
                                "scenarios": [
                                    {"id": "short", "name": "Short", "prompt": "Reply with exactly OK"}
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (state / "benchmark-history.json").write_text(
                json.dumps(
                    [
                        {
                            "runId": "run-1",
                            "mode": "selected",
                            "batteryName": "Default battery",
                            "scenarioName": "Short",
                            "modelId": "model.gguf",
                            "runtime": "TurboQuant",
                            "status": "done",
                            "startedAt": "2026-05-17T09:59:00+00:00",
                            "finishedAt": "2026-05-17T10:00:00+00:00",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            history = [
                {
                    "measuredAt": "2026-05-17T10:00:00+00:00",
                    "label": "test-prompt",
                    "promptTokensPerSecond": 20.0,
                    "completionTokensPerSecond": 30.0,
                    "totalTokensPerSecond": 25.0,
                    "totalMs": 1400.0,
                },
                {
                    "measuredAt": "2026-05-17T10:01:00+00:00",
                    "label": "opencode",
                    "promptTokensPerSecond": 24.0,
                    "completionTokensPerSecond": 36.0,
                    "totalTokensPerSecond": 30.0,
                    "totalMs": 1200.0,
                },
            ]
            history_path.write_text(json.dumps(history), encoding="utf-8")

            with patch(
                "backend.app.services.benchmark_service.detect_local_qwen_home",
                return_value=home,
            ):
                payload = load_benchmark_summary()

        self.assertEqual(payload["historyCount"], 2)
        self.assertEqual(payload["current"]["label"], "opencode")
        self.assertAlmostEqual(payload["averages"]["totalTokensPerSecond"], 27.5)
        self.assertEqual(payload["activity"]["throughputTrend"]["direction"], "up")
        self.assertEqual(len(payload["history"]), 2)
        self.assertEqual(payload["activeRun"]["status"], "idle")
        self.assertEqual(payload["batteries"][0]["name"], "Default battery")
        self.assertEqual(payload["selectedBattery"]["id"], "default")
        self.assertEqual(payload["savedRuns"][0]["runId"], "run-1")
        self.assertTrue(payload["history"][0]["chartLabel"])


if __name__ == "__main__":
    unittest.main()
