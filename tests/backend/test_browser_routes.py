import unittest
from unittest.mock import patch


class BrowserRouteTests(unittest.TestCase):
    def test_browser_catalog_route_returns_service_payload(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"models": [], "refresh": {"counts": {"all": 0, "huggingface": 0, "unsloth": 0}}}
        with patch("backend.app.routes.browser.load_catalog_payload", return_value=expected):
            client = TestClient(app)
            response = client.get("/api/browser/catalog")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_browser_refresh_route_passes_source(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"models": [{"id": "hf-1"}], "refresh": {"counts": {"all": 1, "huggingface": 1, "unsloth": 0}}}
        with patch("backend.app.routes.browser.refresh_catalog", return_value=expected) as service:
            client = TestClient(app)
            response = client.post("/api/browser/catalog/refresh", json={"source": "huggingface"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with(source="huggingface")

    def test_browser_check_compatibility_route_updates_cache_result(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "radi", "checkedAt": "2026-05-17T20:00:00Z", "summary": "staje"}
        with patch("backend.app.routes.browser.check_model_compatibility", return_value=expected) as service:
            client = TestClient(app)
            response = client.post(
                "/api/browser/catalog/check-compatibility",
                json={"modelId": "hf/Qwen3-0.6B-Q8_0.gguf"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with(model_id="hf/Qwen3-0.6B-Q8_0.gguf")

    def test_browser_add_route_uses_huggingface_add_only(self):
        from backend.app.main import app
        from fastapi.testclient import TestClient

        expected = {"status": "ok", "summary": "HF model dodat u spisak: demo.gguf. Sledeci korak je Download."}
        with patch("backend.app.routes.browser.add_catalog_model", return_value=expected) as service:
            client = TestClient(app)
            response = client.post(
                "/api/browser/catalog/add",
                json={
                    "source": "huggingface",
                    "repoId": "Qwen/Qwen3-0.6B-GGUF",
                    "filename": "demo.gguf",
                    "label": "Demo",
                    "family": "Qwen",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with(
            source="huggingface",
            repo_id="Qwen/Qwen3-0.6B-GGUF",
            filename="demo.gguf",
            label="Demo",
            family="Qwen",
        )


if __name__ == "__main__":
    unittest.main()
