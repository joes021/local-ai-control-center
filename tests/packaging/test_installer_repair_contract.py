import pathlib
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]


class InstallerRepairContractTests(unittest.TestCase):
    def test_repair_service_wraps_success_in_human_readable_contract(self):
        from backend.app.services import repair_service

        launcher_payload = {
            "status": "ok",
            "action": "repair-runtime.ps1",
            "summary": "restart-runtime",
            "details": {
                "returncode": 0,
                "stdout": "runtime restarted",
                "stderr": "",
            },
        }

        with mock.patch.object(repair_service, "run_launcher_by_platform", return_value=launcher_payload):
            result = repair_service.run_repair_runtime()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["repairKind"], "runtime")
        self.assertEqual(result["title"], "Popravka runtime-a")
        self.assertEqual(result["summary"], "Popravka runtime-a je zavrsena.")
        self.assertIn("ponovo pokrenemo runtime", result["userMessage"])
        self.assertIn("Home", result["nextStep"])
        self.assertTrue(result["safeForNonTechnicalUsers"])
        self.assertEqual(result["details"]["stdout"], "runtime restarted")

    def test_repair_service_wraps_failure_in_human_readable_contract(self):
        from backend.app.services import repair_service

        launcher_payload = {
            "status": "error",
            "action": "repair-model.sh",
            "summary": "missing-model",
            "details": {
                "returncode": 1,
                "stdout": "",
                "stderr": "model missing",
            },
        }

        with mock.patch.object(repair_service, "run_launcher_by_platform", return_value=launcher_payload):
            result = repair_service.run_repair_model()

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["repairKind"], "model")
        self.assertEqual(result["title"], "Popravka modela")
        self.assertEqual(result["summary"], "Popravka modela nije uspela.")
        self.assertIn("nismo uspeli", result["userMessage"])
        self.assertIn("Detalji", result["nextStep"])
        self.assertTrue(result["safeForNonTechnicalUsers"])
        self.assertEqual(result["details"]["stderr"], "model missing")

    def test_repair_routes_keep_named_repair_endpoints(self):
        content = (ROOT / "backend" / "app" / "routes" / "repair.py").read_text(encoding="utf-8")
        self.assertIn('/api/repair/install', content)
        self.assertIn('/api/repair/model', content)
        self.assertIn('/api/repair/runtime', content)
        self.assertIn('/api/repair/config', content)

    def test_repair_page_explains_safe_repair_flow_for_nontechnical_users(self):
        content = (ROOT / "frontend" / "src" / "pages" / "RepairPage.tsx").read_text(encoding="utf-8")
        self.assertIn("Bezbedan repair tok", content)
        self.assertIn("Popravka instalacije", content)
        self.assertIn("Popravka modela", content)
        self.assertIn("Popravka runtime-a", content)
        self.assertIn("Sledeci korak", content)


if __name__ == "__main__":
    unittest.main()
