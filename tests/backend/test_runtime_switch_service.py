import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class RuntimeSwitchServiceTests(unittest.TestCase):
    def test_select_turboquant_restores_turbo_path_and_marks_choice(self):
        from backend.app.services.runtime_switch_service import select_runtime

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            turbo = home / "apps" / "llama.cpp-turboquant" / "build-cuda" / "bin" / "llama-server"
            llama = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
            turbo.parent.mkdir(parents=True)
            llama.parent.mkdir(parents=True)
            turbo.write_text("turbo", encoding="utf-8")
            llama.write_text("llama", encoding="utf-8")
            (home / "state" / "install-state.json").write_text(
                json.dumps({"llamaServerExe": str(llama), "turboServerExe": ""}),
                encoding="utf-8",
            )
            (home / "state" / "install-report.json").write_text(
                json.dumps(
                    {
                        "components": {
                            "turboQuantRuntime": {"path": str(turbo), "ok": True},
                            "llamaCppRuntime": {"path": str(llama), "ok": True},
                        }
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.runtime_switch_service.run_linux_launcher",
                side_effect=[
                    {"status": "ok", "summary": "stop", "details": {"stdout": "", "stderr": "", "returncode": 0}},
                    {"status": "ok", "summary": "start", "details": {"stdout": "", "stderr": "", "returncode": 0}},
                ],
            ):
                result = select_runtime("turboquant", local_qwen_home=home)

            state = json.loads((home / "state" / "install-state.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "ok")
            self.assertEqual(state["turboServerExe"], str(turbo))

    def test_select_llama_cpp_clears_turbo_server_but_keeps_saved_path(self):
        from backend.app.services.runtime_switch_service import select_runtime

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            turbo = home / "apps" / "llama.cpp-turboquant" / "build-cuda" / "bin" / "llama-server"
            llama = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
            turbo.parent.mkdir(parents=True)
            llama.parent.mkdir(parents=True)
            turbo.write_text("turbo", encoding="utf-8")
            llama.write_text("llama", encoding="utf-8")
            (home / "state" / "install-state.json").write_text(
                json.dumps({"llamaServerExe": str(llama), "turboServerExe": str(turbo)}),
                encoding="utf-8",
            )
            (home / "state" / "install-report.json").write_text(
                json.dumps({"components": {"turboQuantRuntime": {"path": str(turbo), "ok": True}}}),
                encoding="utf-8",
            )

            with patch(
                "backend.app.services.runtime_switch_service.run_linux_launcher",
                side_effect=[
                    {"status": "ok", "summary": "stop", "details": {"stdout": "", "stderr": "", "returncode": 0}},
                    {"status": "ok", "summary": "start", "details": {"stdout": "", "stderr": "", "returncode": 0}},
                ],
            ):
                result = select_runtime("llama.cpp", local_qwen_home=home)

            state = json.loads((home / "state" / "install-state.json").read_text(encoding="utf-8"))
            saved = json.loads((home / "state" / "control-center-next-runtime-choice.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "ok")
            self.assertEqual(state["turboServerExe"], "")
            self.assertEqual(saved["lastTurboServerExe"], str(turbo))


if __name__ == "__main__":
    unittest.main()
