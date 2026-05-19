import json
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


class ModelsServiceTests(unittest.TestCase):
    def test_unsloth_non_mtp_model_is_classified_as_no_mtp(self):
        from backend.app.services import models_service

        status = models_service._classify_mtp_status(
            source="unsloth",
            model_id="unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
            filename="Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
            raw={"source": "unsloth/Qwen3.6-35B-A3B-GGUF"},
        )

        self.assertEqual(status, "no-mtp")

    def test_mtp_variant_is_classified_as_has_mtp(self):
        from backend.app.services import models_service

        status = models_service._classify_mtp_status(
            source="unsloth",
            model_id="unsloth-Qwen3.6-35B-A3B-MTP.gguf",
            filename="Qwen3.6-35B-A3B-MTP.gguf",
            raw={"source": "unsloth/Qwen3.6-35B-A3B-MTP-GGUF"},
        )

        self.assertEqual(status, "has-mtp")

    def test_unsloth_27b_mtp_repo_is_classified_as_has_mtp(self):
        from backend.app.services import models_service

        status = models_service._classify_mtp_status(
            source="unsloth",
            model_id="unsloth-Qwen3.6-27B-MTP-UD-IQ3_S.gguf",
            filename="Qwen3.6-27B-MTP-UD-IQ3_S.gguf",
            raw={"repo": "unsloth/Qwen3.6-27B-MTP-GGUF"},
        )

        self.assertEqual(status, "has-mtp")

    def test_unsloth_27b_non_mtp_repo_is_classified_as_no_mtp(self):
        from backend.app.services import models_service

        status = models_service._classify_mtp_status(
            source="unsloth",
            model_id="unsloth-Qwen3.6-27B-UD-IQ3_XXS.gguf",
            filename="Qwen3.6-27B-UD-IQ3_XXS.gguf",
            raw={"repo": "unsloth/Qwen3.6-27B-GGUF"},
        )

        self.assertEqual(status, "no-mtp")

    def test_unknown_custom_model_is_classified_as_unknown(self):
        from backend.app.services import models_service

        status = models_service._classify_mtp_status(
            source="local",
            model_id="local-demo.gguf",
            filename="demo.gguf",
            raw={},
        )

        self.assertEqual(status, "unknown")

    def test_models_payload_groups_curated_local_hf_and_unsloth_models(self):
        from backend.app.services.models_service import normalize_models

        payload = normalize_models(
            [
                {"id": "qwen36-35b-a3b-IQ2_M.gguf", "source": "curated", "active": True},
                {"id": "local-demo.gguf", "source": "local", "active": False},
                {"id": "hf-Qwen3-0.6B-Q8_0.gguf", "source": "huggingface", "active": False},
                {"id": "unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf", "source": "unsloth", "active": False},
            ]
        )

        self.assertEqual(len(payload["curated"]), 1)
        self.assertEqual(len(payload["local"]), 1)
        self.assertEqual(len(payload["huggingFace"]), 1)
        self.assertEqual(len(payload["unsloth"]), 1)
        self.assertTrue(payload["curated"][0]["active"])

    def test_delete_custom_model_removes_registry_entry_and_file(self):
        from backend.app.services.models_service import delete_model

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            models_dir = home / "models"
            state_dir = home / "state"
            models_dir.mkdir()
            state_dir.mkdir()

            target = models_dir / "demo.gguf"
            target.write_bytes(b"demo")
            registry = state_dir / "custom-models.json"
            registry.write_text(
                """
{
  "models": [
    {
      "id": "local-demo.gguf",
      "filename": "demo.gguf",
      "customSource": "local-file"
    }
  ]
}
""".strip(),
                encoding="utf-8",
            )

            result = delete_model(
                "local-demo.gguf",
                local_qwen_home=home,
                remove_file=True,
                remove_registry=True,
            )

            self.assertEqual(result["status"], "ok")
            self.assertFalse(target.exists())
            self.assertNotIn("local-demo.gguf", registry.read_text(encoding="utf-8"))

    def test_delete_requires_at_least_one_action(self):
        from backend.app.services.models_service import delete_model

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            models_dir = home / "models"
            state_dir = home / "state"
            models_dir.mkdir()
            state_dir.mkdir()
            (home / "config" / "profiles").mkdir(parents=True)
            (home / "config" / "profiles" / "defaults.json").write_text(
                '{"modelChoices":{"demo":{"id":"demo.gguf","filename":"demo.gguf"}}}',
                encoding="utf-8",
            )

            result = delete_model(
                "demo.gguf",
                local_qwen_home=home,
                remove_file=False,
                remove_registry=False,
            )

            self.assertEqual(result["status"], "error")

    def test_windows_add_model_actions_strip_internal_payload(self):
        from backend.app.services import models_service

        raw_result = {
            "status": "ok",
            "action": "Add-UnslothCustomModel",
            "summary": "ok",
            "details": {"returncode": 0, "stdout": "{}", "stderr": ""},
            "payload": {"id": "unsloth-demo.gguf"},
        }

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(models_service, "invoke_windows_common_json", return_value=dict(raw_result)),
        ):
            result = models_service.add_unsloth_model(
                "unsloth/demo",
                "demo.gguf",
                "Demo",
                "Unsloth",
            )

        self.assertEqual(result["status"], "ok")
        self.assertNotIn("payload", result)
        self.assertIn("Unsloth model dodat", result["summary"])
        self.assertEqual(result["details"]["stdout"], "")

    def test_windows_activate_model_refreshes_opencode_config(self):
        from backend.app.services import models_service

        responses = [
            {
                "status": "ok",
                "action": "Set-SelectedModel",
                "summary": "ok",
                "details": {"returncode": 0, "stdout": "selected", "stderr": ""},
                "payload": {"modelId": "demo.gguf"},
            },
            {
                "status": "ok",
                "action": "Update-OpenCodeConfig",
                "summary": "ok",
                "details": {"returncode": 0, "stdout": "OpenCode config: C:\\demo\\opencode.json", "stderr": ""},
                "payload": "C:\\demo\\opencode.json",
            },
        ]

        with (
            mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows"}, clear=False),
            mock.patch.object(models_service, "invoke_windows_common_json", side_effect=responses),
        ):
            result = models_service.activate_model("demo.gguf")

        self.assertEqual(result["status"], "ok")
        self.assertIn("OpenCode config je osvezen", result["summary"])
        self.assertIn("OpenCode config:", result["details"]["stdout"])

    def test_load_download_progress_payload_reads_live_progress_file(self):
        from backend.app.services import models_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            state_dir = home / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "model-download-progress.json").write_text(
                """
{
  "status": "downloading",
  "modelId": "unsloth-demo.gguf",
  "fileName": "demo.gguf",
  "source": "unsloth/demo",
  "downloadedGiB": 1.5,
  "totalGiB": 10.0,
  "speedMBps": 42.0,
  "etaSeconds": 180,
  "percent": 15.0,
  "message": "Preuzimanje u toku",
  "updatedAt": 1778982103.3022773
}
""".strip(),
                encoding="utf-8",
            )

            with mock.patch.object(models_service, "detect_local_qwen_home", return_value=home):
                payload = models_service.load_download_progress_payload()

        self.assertEqual(payload["status"], "downloading")
        self.assertTrue(payload["isActive"])
        self.assertEqual(payload["modelId"], "unsloth-demo.gguf")
        self.assertEqual(payload["percent"], 15.0)
        self.assertEqual(payload["speedMBps"], 42.0)
        self.assertEqual(payload["etaSeconds"], 180)

    def test_windows_download_model_spawns_detached_worker_and_writes_starting_progress(self):
        from backend.app.services import models_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            launchers = home / "launchers"
            state_dir = home / "state"
            launchers.mkdir(parents=True)
            state_dir.mkdir(parents=True)
            (launchers / "manage-models.ps1").write_text("# demo", encoding="utf-8")

            fake_process = mock.Mock(pid=4321)
            with (
                mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "windows", "SystemRoot": r"C:\Windows"}, clear=False),
                mock.patch.object(models_service, "detect_local_qwen_home", return_value=home),
                mock.patch.object(models_service.subprocess, "Popen", return_value=fake_process) as popen_mock,
            ):
                result = models_service.download_model("hf-demo.gguf")

            self.assertEqual(result["status"], "ok")
            kwargs = popen_mock.call_args.kwargs
            self.assertTrue(kwargs["close_fds"])
            self.assertNotEqual(kwargs["creationflags"], 0)
            progress = json.loads((state_dir / "model-download-progress.json").read_text(encoding="utf-8"))
            self.assertEqual(progress["status"], "starting")
            self.assertEqual(progress["modelId"], "hf-demo.gguf")
            self.assertIsInstance(progress["updatedAt"], float)

    def test_detected_active_model_outside_models_dir_is_marked_installed(self):
        from backend.app.services import models_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            models_dir = home / "models"
            state_dir = home / "state"
            external_dir = home / "external-models"
            models_dir.mkdir()
            state_dir.mkdir()
            external_dir.mkdir()
            model_path = external_dir / "Qwen3.6-35B-A3B-MXFP4_MOE.gguf"
            model_path.write_bytes(b"demo-bytes")

            entry = models_service._build_detected_active_model_entry(
                install_state={"modelId": model_path.name, "modelFile": str(model_path)},
                models_dir=models_dir,
                active_model_id=model_path.name,
                seen_ids=set(),
            )

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertTrue(entry["installed"])
        self.assertAlmostEqual(entry["installedSizeGiB"], 0.0, places=2)

    def test_activate_model_falls_back_to_detected_local_file_when_launcher_cannot_resolve_id(self):
        from backend.app.services import models_service

        with TemporaryDirectory() as tmp:
            fake_home = Path(tmp)
            state_dir = fake_home / "state"
            llama_models_dir = fake_home / "models" / "llama-cpp"
            state_dir.mkdir(parents=True)
            llama_models_dir.mkdir(parents=True)
            target_model = llama_models_dir / "Qwen3.6-35B-A3B-MXFP4_MOE.gguf"
            target_model.write_bytes(b"demo")
            (state_dir / "install-state.json").write_text(
                json.dumps({"modelId": "old.gguf", "modelFile": "/tmp/old.gguf"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with (
                mock.patch.object(models_service, "detect_local_qwen_home", return_value=fake_home),
                mock.patch.object(
                    models_service,
                    "run_linux_launcher",
                    side_effect=[
                        {
                            "status": "error",
                            "action": "manage-models.sh",
                            "summary": "Model nije pronadjen: Qwen3.6-35B-A3B-MXFP4_MOE.gguf",
                            "details": {"returncode": 1, "stdout": "", "stderr": "missing"},
                        },
                        {
                            "status": "ok",
                            "action": "configure-settings.sh",
                            "summary": "ok",
                            "details": {"returncode": 0, "stdout": "configured", "stderr": ""},
                        },
                    ],
                ),
                mock.patch.object(Path, "home", return_value=fake_home),
                mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "linux"}, clear=False),
                mock.patch.object(models_service, "load_model_override_payload", return_value={}),
                mock.patch.object(models_service, "load_global_defaults_payload", return_value={}),
            ):
                result = models_service.activate_model(target_model.name)

            self.assertEqual(result["status"], "ok")
            updated_state = json.loads((state_dir / "install-state.json").read_text(encoding="utf-8"))
            self.assertEqual(updated_state["modelId"], target_model.name)
            self.assertEqual(updated_state["modelFile"], str(target_model))

    def test_load_download_progress_payload_returns_idle_without_file(self):
        from backend.app.services import models_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "state").mkdir(parents=True)
            with mock.patch.object(models_service, "detect_local_qwen_home", return_value=home):
                payload = models_service.load_download_progress_payload()

        self.assertEqual(payload["status"], "idle")
        self.assertFalse(payload["isActive"])

    def test_load_models_payload_includes_detected_active_model_from_install_state(self):
        from backend.app.services import models_service

        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            models_dir = home / "models"
            state_dir = home / "state"
            profiles_dir = home / "config" / "profiles"
            models_dir.mkdir(parents=True)
            state_dir.mkdir(parents=True)
            profiles_dir.mkdir(parents=True)

            active_file = models_dir / "Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf"
            active_file.write_bytes(b"demo")
            (profiles_dir / "defaults.json").write_text('{"modelChoices":{}}', encoding="utf-8")
            (state_dir / "custom-models.json").write_text('{"models":[]}', encoding="utf-8")
            (state_dir / "install-state.json").write_text(
                json.dumps(
                    {
                        "modelId": "qwen-active-demo",
                        "modelFile": str(active_file),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            with mock.patch.object(models_service, "detect_local_qwen_home", return_value=home):
                payload = models_service.load_models_payload()

        self.assertEqual(len(payload["local"]), 1)
        detected = payload["local"][0]
        self.assertEqual(detected["id"], "qwen-active-demo")
        self.assertTrue(detected["active"])
        self.assertTrue(detected["installed"])
        self.assertEqual(detected["filename"], "Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf")
        self.assertEqual(detected["family"], "Qwen")

    def test_detect_local_qwen_home_prefers_new_linux_path(self):
        from backend.app.services import local_qwen_paths

        with TemporaryDirectory() as tmp:
            fake_home = Path(tmp)
            new_default = fake_home / "local-ai-control-center"

            with (
                mock.patch.dict("os.environ", {}, clear=True),
                mock.patch.object(local_qwen_paths, "get_target_platform", return_value="linux"),
                mock.patch.object(Path, "home", return_value=fake_home),
            ):
                detected = local_qwen_paths.detect_local_qwen_home()

            self.assertEqual(detected, new_default)

            new_default.mkdir()
            with (
                mock.patch.dict("os.environ", {}, clear=True),
                mock.patch.object(local_qwen_paths, "get_target_platform", return_value="linux"),
                mock.patch.object(Path, "home", return_value=fake_home),
            ):
                detected = local_qwen_paths.detect_local_qwen_home()

            self.assertEqual(detected, new_default)

    def test_detect_local_qwen_home_uses_local_ai_control_center_on_windows(self):
        from backend.app.services import local_qwen_paths

        with TemporaryDirectory() as tmp:
            fake_home = Path(tmp)

            with (
                mock.patch.dict("os.environ", {}, clear=True),
                mock.patch.object(local_qwen_paths, "get_target_platform", return_value="windows"),
                mock.patch.object(Path, "home", return_value=fake_home),
            ):
                detected = local_qwen_paths.detect_local_qwen_home()

            self.assertEqual(detected, fake_home / "LocalAIControlCenter")

    def test_complete_model_action_updates_registry(self):
        from backend.app.services import models_service

        action_id = f"action-{uuid.uuid4()}"
        with mock.patch.object(models_service, "_MODEL_ACTIONS", {}):
            models_service._MODEL_ACTIONS[action_id] = {
                "status": "pending",
                "summary": "start",
                "result": None,
            }
            models_service.complete_model_action(
                action_id,
                {
                    "status": "ok",
                    "action": "models",
                    "summary": "zavrseno",
                    "details": {"returncode": 0, "stdout": "", "stderr": ""},
                },
            )
            payload = models_service.get_model_action_status(action_id)

        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["isDone"])
        self.assertEqual(payload["result"]["summary"], "zavrseno")


if __name__ == "__main__":
    unittest.main()
