import unittest
from unittest.mock import patch


class BenchmarkRouteTests(unittest.TestCase):
    def test_benchmark_route_returns_service_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {
            "historyCount": 2,
            "current": {"label": "opencode"},
            "liveCurrent": {"label": "opencode-live"},
            "averages": {"totalTokensPerSecond": 27.5},
            "activity": {"throughputTrend": {"direction": "up"}},
            "history": [],
            "liveHistory": [],
        }

        with patch(
            "backend.app.routes.benchmark.load_benchmark_summary",
            return_value=expected,
        ):
            client = TestClient(app)
            response = client.get("/api/benchmark")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_benchmark_run_selected_route_returns_service_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "accepted", "summary": "pokrenuto", "runId": "run-1"}

        with patch(
            "backend.app.routes.benchmark.start_selected_benchmark",
            return_value=expected,
        ):
            client = TestClient(app)
            response = client.post(
                "/api/benchmark/run-selected",
                json={"scenarioId": "short"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_benchmark_clear_history_route_returns_service_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "ok", "summary": "obrisano"}

        with patch(
            "backend.app.routes.benchmark.clear_benchmark_history",
            return_value=expected,
        ):
            client = TestClient(app)
            response = client.post("/api/benchmark/clear-history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)


if __name__ == "__main__":
    unittest.main()
