import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


class BenchmarkServiceTests(unittest.TestCase):
    def test_load_runtime_server_port_reads_install_state(self):
        from backend.app.services.benchmark_service import _load_runtime_server_port

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            state = home / "state"
            state.mkdir(parents=True, exist_ok=True)
            (state / "install-state.json").write_text(json.dumps({"port": 8091}), encoding="utf-8")

            with patch(
                "backend.app.services.benchmark_service.detect_local_qwen_home",
                return_value=home,
            ):
                port = _load_runtime_server_port()

        self.assertEqual(port, 8091)

    def test_load_benchmark_summary_reads_history_and_builds_metrics(self):
        from backend.app.services.benchmark_service import load_benchmark_summary

        with tempfile.TemporaryDirectory() as temp_dir:
            now = datetime.now(timezone.utc)
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
                    "measuredAt": (now - timedelta(seconds=60)).isoformat(),
                    "label": "test-prompt",
                    "promptTokensPerSecond": 20.0,
                    "completionTokensPerSecond": 30.0,
                    "totalTokensPerSecond": 25.0,
                    "totalMs": 1400.0,
                },
                {
                    "measuredAt": (now - timedelta(seconds=30)).isoformat(),
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
        self.assertEqual(payload["liveCurrent"], None)
        self.assertAlmostEqual(payload["averages"]["totalTokensPerSecond"], 27.5)
        self.assertEqual(payload["activity"]["throughputTrend"]["direction"], "up")
        self.assertEqual(len(payload["history"]), 2)
        self.assertEqual(payload["liveHistory"], [])
        self.assertEqual(payload["activeRun"]["status"], "idle")
        self.assertEqual(payload["batteries"][0]["name"], "Default battery")
        self.assertEqual(payload["selectedBattery"]["id"], "default")
        self.assertEqual(payload["savedRuns"][0]["runId"], "run-1")
        self.assertTrue(payload["history"][0]["chartLabel"])

    def test_load_benchmark_summary_merges_live_slot_metric_into_signal_history(self):
        from backend.app.services.benchmark_service import load_benchmark_summary

        with tempfile.TemporaryDirectory() as temp_dir:
            now = datetime.now(timezone.utc)
            home = Path(temp_dir)
            state = home / "state"
            state.mkdir(parents=True, exist_ok=True)
            (state / "benchmark-batteries.json").write_text(
                json.dumps(
                    {
                        "activeBatteryId": "default",
                        "batteries": [
                            {
                                "id": "default",
                                "name": "Default battery",
                                "source": "default",
                                "scenarios": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (state / "token-metrics-history.json").write_text(
                json.dumps(
                    [
                        {
                            "measuredAt": (now - timedelta(seconds=30)).isoformat(),
                            "label": "test-prompt",
                            "promptTokensPerSecond": 20.0,
                            "completionTokensPerSecond": 30.0,
                            "totalTokensPerSecond": 25.0,
                            "totalMs": 1400.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            live_sample = {
                "measuredAt": (now - timedelta(seconds=5)).isoformat(),
                "label": "opencode-live",
                "promptTokensPerSecond": 0.0,
                "completionTokensPerSecond": 12.0,
                "totalTokensPerSecond": 12.0,
                "totalMs": 5000.0,
            }

            with patch(
                "backend.app.services.benchmark_service.detect_local_qwen_home",
                return_value=home,
            ), patch(
                "backend.app.services.benchmark_service._load_live_slot_metric",
                return_value=live_sample,
            ):
                payload = load_benchmark_summary()

        self.assertEqual(payload["historyCount"], 1)
        self.assertEqual(payload["requestCount"], 1)
        self.assertEqual(payload["current"]["label"], "opencode-live")
        self.assertEqual(payload["liveCurrent"]["label"], "opencode-live")
        self.assertEqual(payload["history"][-1]["label"], "opencode-live")
        self.assertEqual(payload["liveHistory"][-1]["label"], "opencode-live")
        self.assertEqual(payload["activity"]["sources"]["opencode"], 1)
        self.assertEqual(payload["averages"]["totalTokensPerSecond"], 25.0)

    def test_load_benchmark_summary_preserves_recent_live_history_between_polls(self):
        from backend.app.services.benchmark_service import load_benchmark_summary

        with tempfile.TemporaryDirectory() as temp_dir:
            now = datetime.now(timezone.utc)
            home = Path(temp_dir)
            state = home / "state"
            state.mkdir(parents=True, exist_ok=True)
            (state / "benchmark-batteries.json").write_text(
                json.dumps(
                    {
                        "activeBatteryId": "default",
                        "batteries": [{"id": "default", "name": "Default battery", "source": "default", "scenarios": []}],
                    }
                ),
                encoding="utf-8",
            )
            (state / "token-metrics-history.json").write_text(
                json.dumps(
                    [
                        {
                            "measuredAt": (now - timedelta(seconds=30)).isoformat(),
                            "label": "test-prompt",
                            "promptTokensPerSecond": 20.0,
                            "completionTokensPerSecond": 30.0,
                            "totalTokensPerSecond": 25.0,
                            "totalMs": 1400.0,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            live_sample = {
                "measuredAt": (now - timedelta(seconds=5)).isoformat(),
                "label": "opencode-live",
                "promptTokensPerSecond": 0.0,
                "completionTokensPerSecond": 12.0,
                "totalTokensPerSecond": 12.0,
                "totalMs": 5000.0,
                "signature": "opencode-live:sample-1",
            }

            with patch(
                "backend.app.services.benchmark_service.detect_local_qwen_home",
                return_value=home,
            ), patch(
                "backend.app.services.benchmark_service._load_live_slot_metric",
                side_effect=[live_sample, None],
            ):
                first = load_benchmark_summary()
                second = load_benchmark_summary()

        self.assertEqual(first["current"]["label"], "opencode-live")
        self.assertEqual(first["liveCurrent"]["label"], "opencode-live")
        self.assertEqual(second["current"]["label"], "opencode-live")
        self.assertEqual(second["liveCurrent"]["label"], "opencode-live")
        self.assertEqual(second["history"][-1]["label"], "opencode-live")
        self.assertEqual(second["liveHistory"][-1]["label"], "opencode-live")
        self.assertEqual(second["activity"]["sources"]["opencode"], 1)

    def test_load_live_slot_metric_uses_extended_timeout(self):
        from backend.app.services.benchmark_service import (
            LIVE_SLOTS_TIMEOUT_SECONDS,
            _load_live_slot_metric,
        )

        mocked_response = MagicMock()
        mocked_response.__enter__.return_value.read.return_value = b"[]"

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            state = home / "state"
            state.mkdir(parents=True, exist_ok=True)
            (state / "install-state.json").write_text(json.dumps({"port": 8091}), encoding="utf-8")

            with patch(
                "backend.app.services.benchmark_service.detect_local_qwen_home",
                return_value=home,
            ), patch(
                "backend.app.services.benchmark_service.urlopen",
                return_value=mocked_response,
            ) as mocked_urlopen:
                _load_live_slot_metric()

        mocked_urlopen.assert_called_once_with(
            "http://127.0.0.1:8091/slots",
            timeout=LIVE_SLOTS_TIMEOUT_SECONDS,
        )

    def test_clear_benchmark_history_resets_files(self):
        from backend.app.services.benchmark_service import clear_benchmark_history

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            state = home / "state"
            state.mkdir(parents=True, exist_ok=True)
            (state / "token-metrics-history.json").write_text(json.dumps([{"label": "x"}]), encoding="utf-8")
            (state / "benchmark-history.json").write_text(json.dumps([{"runId": "run-1"}]), encoding="utf-8")
            (state / "benchmark-live-history.json").write_text(json.dumps([{"label": "live"}]), encoding="utf-8")
            (state / "benchmark-live-slots.json").write_text(json.dumps({"entries": [{"slot": 1}]}), encoding="utf-8")

            with patch(
                "backend.app.services.benchmark_service.detect_local_qwen_home",
                return_value=home,
            ):
                payload = clear_benchmark_history()

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(json.loads((state / "token-metrics-history.json").read_text(encoding="utf-8")), [])
            self.assertEqual(json.loads((state / "benchmark-history.json").read_text(encoding="utf-8")), [])
            self.assertEqual(json.loads((state / "benchmark-live-history.json").read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
