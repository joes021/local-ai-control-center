import unittest
from unittest.mock import patch


class ServerRouteTests(unittest.TestCase):
    def test_server_status_route_returns_service_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {
            "status": "active",
            "health": "ok",
            "port": 8091,
            "activeModel": "model.gguf",
        }

        with patch(
            "backend.app.routes.server.load_server_status",
            return_value=expected,
        ):
            client = TestClient(app)
            response = client.get("/api/server/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_server_start_route_invokes_service(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "ok", "summary": "started"}
        with patch(
            "backend.app.routes.server.start_server",
            return_value=expected,
        ) as service:
            client = TestClient(app)
            response = client.post("/api/server/start")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with()

    def test_server_stop_route_invokes_service(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "ok", "summary": "stopped"}
        with patch(
            "backend.app.routes.server.stop_server",
            return_value=expected,
        ) as service:
            client = TestClient(app)
            response = client.post("/api/server/stop")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with()

    def test_server_open_web_route_invokes_service(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "ok", "summary": "opened"}
        with patch(
            "backend.app.routes.server.open_server_web",
            return_value=expected,
        ) as service:
            client = TestClient(app)
            response = client.post("/api/server/open-web")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
