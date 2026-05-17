# Windows Parity Phase 1: MTP Truth And OpenCode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make MTP labels come from real Unsloth/source truth and restore essential OpenCode functionality in the new Windows Web UI.

**Architecture:** First, tighten backend model metadata so MTP state is derived from real repo/source families instead of weak heuristics. Then add a Windows-aware OpenCode backend adapter and surface it in the Web UI through Home and Settings so the new UI regains critical parity with the old Windows control center.

**Tech Stack:** Python backend services, FastAPI routes, existing Windows PowerShell launcher scripts, React + TypeScript frontend, Python `unittest`, Vite build.

---

## File Structure

- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\models_service.py`
  - Replace loose MTP inference with source-truth classification.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_models_service.py`
  - Add tests for real repo-based MTP classification.
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\opencode_service.py`
  - Centralize OpenCode status, launch, and settings adapter logic.
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\opencode.py`
  - Expose OpenCode API endpoints.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\main.py`
  - Register OpenCode router.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\settings_service.py`
  - Reuse/extend OpenCode-related settings payload where needed.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`
  - Add OpenCode status and settings types.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts`
  - Add OpenCode fetch/apply/launch API calls.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\HomePage.tsx`
  - Add OpenCode status card and launch action.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\SettingsPage.tsx`
  - Add OpenCode settings section.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`
  - Add smoke assertions for OpenCode parity UI.
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_opencode_service.py`
  - Verify OpenCode backend behavior.

## Task 1: Make MTP classification use real source truth

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\models_service.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_models_service.py`

- [ ] **Step 1: Add failing tests for real repo-family MTP truth**

Add tests that verify:

- `unsloth/Qwen3.6-35B-A3B-GGUF` => `no-mtp`
- `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` => `has-mtp`
- `unsloth/Qwen3.6-27B-GGUF` => `no-mtp`
- `unsloth/Qwen3.6-27B-MTP-GGUF` => `has-mtp`

Example:

```python
def test_unsloth_35b_non_mtp_repo_is_no_mtp(self):
    from backend.app.services import models_service

    status = models_service._classify_mtp_status(
        source="unsloth",
        model_id="unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
        filename="Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
        raw={"source": "unsloth/Qwen3.6-35B-A3B-GGUF"},
    )

    self.assertEqual(status, "no-mtp")
```

- [ ] **Step 2: Run backend MTP tests and confirm failure if needed**

Run:

```bash
python -m unittest tests.backend.test_models_service
```

Expected: FAIL if source-truth classification is not yet precise enough.

- [ ] **Step 3: Tighten `_classify_mtp_status`**

In `models_service.py`, prefer explicit repo-family rules before general string heuristics.

Recommended rule shape:

```python
repo = str(raw.get("source", "") or "").lower()

if repo in {
    "unsloth/qwen3.6-35b-a3b-mtp-gguf",
    "unsloth/qwen3.6-35b-a3b-gguf-mtp",
    "unsloth/qwen3.6-27b-mtp-gguf",
    "unsloth/qwen3.6-27b-gguf-mtp",
}:
    return "has-mtp"

if repo in {
    "unsloth/qwen3.6-35b-a3b-gguf",
    "unsloth/qwen3.6-27b-gguf",
}:
    return "no-mtp"
```

Then only use filename/repo substring fallback for everything else.

- [ ] **Step 4: Run backend tests again**

Run:

```bash
python -m unittest tests.backend.test_models_service
```

Expected: PASS

- [ ] **Step 5: Commit MTP truth changes**

```bash
git add backend/app/services/models_service.py tests/backend/test_models_service.py
git commit -m "feat: derive mtp status from real unsloth source families"
```

## Task 2: Add OpenCode backend service

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\opencode_service.py`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_opencode_service.py`

- [ ] **Step 1: Write failing backend tests for OpenCode status**

Add tests that verify the service can:

- return executable availability
- return config availability/path
- expose working directory
- expose build/plan/general/explore steps
- expose security/capability mode if available

Example:

```python
def test_load_opencode_status_payload_contains_basic_fields(self):
    from backend.app.services import opencode_service

    payload = opencode_service.load_opencode_status_payload(...)

    self.assertIn("available", payload)
    self.assertIn("configExists", payload)
    self.assertIn("configPath", payload)
```

- [ ] **Step 2: Run the new backend test and confirm failure**

Run:

```bash
python -m unittest tests.backend.test_opencode_service
```

Expected: FAIL because the service file does not exist yet.

- [ ] **Step 3: Implement `opencode_service.py`**

Use the existing stable Windows scripts as source of truth, preferably through existing shared helpers or platform-aware script calls.

The service should provide:

- `load_opencode_status_payload()`
- `launch_opencode()`
- `load_opencode_settings_payload()`
- `apply_opencode_settings(payload)`

Minimum returned fields:

- `available`
- `configExists`
- `configPath`
- `configDir`
- `workingDirectory`
- `buildSteps`
- `planSteps`
- `generalSteps`
- `exploreSteps`
- `securityMode`
- `capabilityMode`

- [ ] **Step 4: Re-run OpenCode backend tests**

Run:

```bash
python -m unittest tests.backend.test_opencode_service
```

Expected: PASS

- [ ] **Step 5: Commit backend OpenCode service**

```bash
git add backend/app/services/opencode_service.py tests/backend/test_opencode_service.py
git commit -m "feat: add opencode backend service for control center next"
```

## Task 3: Add OpenCode API routes

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\opencode.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\main.py`

- [ ] **Step 1: Add route tests or smoke assumptions**

If route-specific tests are already lightweight in this repo, add a minimal smoke test. If not, use service-level tests plus later HTTP smoke verification.

- [ ] **Step 2: Implement routes**

Expose:

- `GET /api/opencode/status`
- `POST /api/opencode/open`
- `GET /api/opencode/settings`
- `POST /api/opencode/settings/apply`

- [ ] **Step 3: Register router in `main.py`**

Add:

```python
from backend.app.routes import opencode
app.include_router(opencode.router)
```

- [ ] **Step 4: Run focused backend tests**

Run:

```bash
python -m unittest tests.backend.test_opencode_service tests.backend.test_platform_services
```

Expected: PASS

- [ ] **Step 5: Commit the route layer**

```bash
git add backend/app/routes/opencode.py backend/app/main.py
git commit -m "feat: expose opencode api routes"
```

## Task 4: Add frontend OpenCode API and types

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts`

- [ ] **Step 1: Add OpenCode types**

Create types such as:

```ts
export type OpenCodeStatusPayload = {
  available: boolean;
  configExists: boolean;
  configPath: string;
  configDir: string;
  workingDirectory: string;
  buildSteps: number;
  planSteps: number;
  generalSteps: number;
  exploreSteps: number;
  securityMode: string;
  capabilityMode: string;
};
```

- [ ] **Step 2: Add OpenCode API helpers**

Add:

- `fetchOpenCodeStatus()`
- `fetchOpenCodeSettings()`
- `applyOpenCodeSettings()`
- `openOpenCode()`

- [ ] **Step 3: Run TypeScript build**

Run:

```bash
node .\node_modules\typescript\bin\tsc -b
```

Expected: PASS or only fail because UI pages are not updated yet.

- [ ] **Step 4: Commit frontend API/types layer**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts
git commit -m "feat: add frontend opencode api and types"
```

## Task 5: Add OpenCode section to Home page

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\HomePage.tsx`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`

- [ ] **Step 1: Add failing smoke assertions**

Add checks for strings such as:

```python
self.assertIn("OpenCode", content)
self.assertIn("Open OpenCode", content)
self.assertIn("OpenCode config", content)
```

- [ ] **Step 2: Run smoke tests and confirm failure**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: FAIL

- [ ] **Step 3: Implement Home page OpenCode block**

Add:

- OpenCode availability status
- config status/path
- `Open OpenCode` button

If not available:

- show `nije dostupan`
- show short reason if present

- [ ] **Step 4: Re-run smoke tests**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 5: Commit Home page changes**

```bash
git add frontend/src/pages/HomePage.tsx tests/frontend/test_ui_source_smoke.py
git commit -m "feat: add opencode home panel to windows web ui"
```

## Task 6: Add OpenCode settings to Settings page

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\SettingsPage.tsx`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`

- [ ] **Step 1: Add failing smoke assertions for missing OpenCode settings**

Add checks for:

- `Working directory`
- `Security mode`
- `Capability mode`
- `OpenCode config`

- [ ] **Step 2: Run smoke tests and confirm failure**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: FAIL

- [ ] **Step 3: Implement OpenCode settings section**

Show and edit:

- working directory
- build steps
- plan steps
- general steps
- explore steps
- security mode
- capability mode

Prefer using existing backend payload values, not duplicating state assumptions in the browser.

- [ ] **Step 4: Wire save/apply action**

Ensure the settings page can submit OpenCode changes through the new OpenCode settings apply route.

- [ ] **Step 5: Re-run frontend smoke tests**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 6: Build frontend**

Run:

```bash
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

Expected: PASS

- [ ] **Step 7: Commit Settings page parity changes**

```bash
git add frontend/src/pages/SettingsPage.tsx tests/frontend/test_ui_source_smoke.py
git commit -m "feat: restore opencode settings in windows web ui"
```

## Task 7: Final verification

**Files:**
- No new source files; verification only

- [ ] **Step 1: Run focused parity tests**

Run:

```bash
python -m unittest tests.backend.test_models_service tests.backend.test_opencode_service tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 2: Run the broader GUI suite**

Run:

```bash
python -m unittest tests.backend.test_models_service tests.backend.test_opencode_service tests.backend.test_status_service tests.backend.test_platform_services tests.backend.test_script_runner tests.backend.test_settings_service tests.backend.test_native_dialogs tests.launchers.test_windows_launcher_smoke tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 3: Run production frontend build**

Run:

```bash
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

Expected: PASS

- [ ] **Step 4: Manual Windows verification**

Verify in the running UI:

- Unsloth model cards show correct MTP status based on real repo family
- `Open OpenCode` is visible and functional
- OpenCode availability/config status are visible
- OpenCode settings can be viewed and edited

- [ ] **Step 5: Confirm clean git state or intentional staged work**

Run:

```bash
git status
```

Expected: only the intended changes remain.

## Notes

- Do not attempt benchmark parity in this phase.
- Prefer stable-script reuse over inventing new OpenCode logic in the new backend.
- If old Windows UI uses multiple OpenCode-related state sources, normalize them in the backend service rather than scattering the logic in React.
