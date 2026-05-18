import unittest
from unittest.mock import patch


class CompatibilityRouteTests(unittest.TestCase):
    def test_check_route_passes_browser_model_id(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"fitLabel": "Radi", "summary": "ok", "status": "radi"}
        with patch("backend.app.routes.compatibility.run_compatibility_check", return_value=expected) as service:
            client = TestClient(app)
            response = client.post("/api/compatibility/check", json={"catalogModelId": "unsloth/demo/demo.gguf"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once()

    def test_check_route_accepts_inline_model_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"fitLabel": "Granicno", "summary": "ok", "status": "granicno"}
        with patch("backend.app.routes.compatibility.run_compatibility_check", return_value=expected) as service:
            client = TestClient(app)
            response = client.post(
                "/api/compatibility/check",
                json={"model": {"id": "local/demo.gguf", "label": "Demo", "approxSizeGiB": 6.4}},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once()

    def test_apply_route_passes_action_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {
            "result": {"status": "ok", "summary": "primenjeno"},
            "compatibility": {"status": "granicno", "fitLabel": "Granicno", "summary": "ponovo provereno"},
        }
        with patch("backend.app.routes.compatibility.apply_compatibility_action", return_value=expected) as service:
            client = TestClient(app)
            response = client.post(
                "/api/compatibility/apply",
                json={
                    "catalogModelId": "unsloth/demo/demo.gguf",
                    "action": {"kind": "set-context", "value": 131072},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once()


if __name__ == "__main__":
    unittest.main()
