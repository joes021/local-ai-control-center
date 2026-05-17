# Server Control Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vratiti u `Control Center Next` upravljanje `llama.cpp` serverom kroz zajednički Web UI, sa server status panelom, `Start/Stop server` akcijama i `Run llama.cpp web` tokom za Windows i Linux.

**Architecture:** Novi backend dobija poseban `server` servis i rute koje koriste postojeće stable launchere kao izvor istine. Frontend dobija novi `Server` blok na `Home` strani koji prikazuje lifecycle stanje i akcije, dok OS-specifične razlike ostaju zatvorene u backend adapterima.

**Tech Stack:** FastAPI backend, React + Vite frontend, Python `unittest`, postojeći PowerShell/Bash launcher adapteri

---

## File Structure

### Existing files to modify

- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\main.py`
  - Registracija novih `server` API ruta.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\script_runner.py`
  - Po potrebi proširenje helpera za platform-specific start/stop/open-web tokove.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\local_qwen_state.py`
  - Deljenje lifecycle/status parsiranja sa novim server servisom ako treba.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts`
  - Novi `server` API helperi.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`
  - Novi `ServerStatusPayload` tip.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\HomePage.tsx`
  - Novi `Server` blok i akcije.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`
  - Smoke provere za novi `Server` blok.

### New files to create

- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\server.py`
  - `GET /api/server/status`
  - `POST /api/server/start`
  - `POST /api/server/stop`
  - `POST /api/server/open-web`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py`
  - Centralni adapter za server lifecycle/status.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_server_service.py`
  - Backend TDD za status/start/stop/open-web.

### Stable repo files likely to inspect or reuse

- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows\start-server.ps1`
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows\stop-server.ps1`
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows\open-web-ui.ps1` or equivalent launcher if present
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows\local-qwen-common.ps1`
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux\start-server.sh`
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux\stop-server.sh`
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux\local_qwen_common.sh`

## Task 1: Discover stable server lifecycle entrypoints

**Files:**
- Inspect: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows\*.ps1`
- Inspect: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux\*.sh`
- Note findings in: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py`

- [ ] **Step 1: Identify Windows server scripts and common helpers**

Run:
```powershell
rg -n "start-server|stop-server|web|health|server-lifecycle|llama.cpp je pokrenut|Stop llama.cpp server" "C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows"
```

Expected: references to start/stop server and lifecycle helpers.

- [ ] **Step 2: Identify Linux server scripts and common helpers**

Run:
```powershell
rg -n "start-server|stop-server|web|health|server-lifecycle|llama.cpp" "C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux"
```

Expected: Linux equivalents for start/stop/lifecycle.

- [ ] **Step 3: Record which scripts should back each new API route**

Document in code comments or temporary notes:
- Windows start -> exact script
- Windows stop -> exact script
- Windows open web -> exact script or fallback URL open strategy
- Linux start -> exact script
- Linux stop -> exact script
- Linux open web -> exact script or fallback URL open strategy

- [ ] **Step 4: Commit discovery-only notes if needed**

```bash
git add C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py
git commit -m "chore: capture server lifecycle integration notes"
```

Only commit if code comments/notes were actually added.

## Task 2: Add failing backend tests for server service

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_server_service.py`

- [ ] **Step 1: Write failing test for idle server status payload**

```python
def test_load_server_status_returns_expected_fields_for_idle_state(self):
    payload = load_server_status(...)
    self.assertIn("status", payload)
    self.assertIn("port", payload)
    self.assertIn("health", payload)
    self.assertIn("pid", payload)
    self.assertIn("message", payload)
    self.assertIn("localUrl", payload)
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:
```powershell
python -m unittest tests.backend.test_server_service
```

Expected: FAIL because module/function does not exist yet.

- [ ] **Step 3: Add failing tests for start/stop/open-web actions**

Add tests for:
- `start_server()` returns action payload
- `stop_server()` returns action payload
- `open_server_web()` returns action payload
- platform adapter chooses Windows/Linux scripts correctly

- [ ] **Step 4: Re-run the backend test file**

Run:
```powershell
python -m unittest tests.backend.test_server_service
```

Expected: FAIL on missing implementation, not syntax errors.

## Task 3: Implement backend server service

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\script_runner.py`
- Inspect: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\local_qwen_state.py`

- [ ] **Step 1: Create minimal `server_service.py` skeleton**

Implement stubs:
```python
def load_server_status(...): ...
def start_server(...): ...
def stop_server(...): ...
def open_server_web(...): ...
```

- [ ] **Step 2: Implement status payload from existing lifecycle and install state**

Payload should include:
- `status`
- `health`
- `port`
- `pid`
- `activeRuntime`
- `message`
- `localUrl`
- `tailscaleUrl`
- `canOpenWeb`

Prefer existing lifecycle/status data over invented state.

- [ ] **Step 3: Implement Windows/Linux start adapter**

Use stable launcher script names through existing script-runner helpers.

Expected behavior:
- return accepted/ok payload
- include meaningful summary
- avoid raw shell output as only user-facing explanation

- [ ] **Step 4: Implement Windows/Linux stop adapter**

Use stable stop scripts.
If server is already inactive, return informative success-like response rather than generic error where possible.

- [ ] **Step 5: Implement open-web adapter**

Use stable launcher if present.
If not present, use best supported local URL open path per OS adapter.

- [ ] **Step 6: Run backend tests to get green**

Run:
```powershell
python -m unittest tests.backend.test_server_service
```

Expected: PASS

- [ ] **Step 7: Commit backend server service**

```bash
git add C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_server_service.py C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\script_runner.py
git commit -m "feat: add server lifecycle backend service"
```

## Task 4: Add server API routes

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\server.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\main.py`

- [ ] **Step 1: Write failing route smoke tests if needed**

If route-level tests are not practical, extend backend service tests with route invocation expectations through FastAPI import-level smoke assumptions.

- [ ] **Step 2: Add server router with exact routes**

Implement:
```python
@router.get("/api/server/status")
@router.post("/api/server/start")
@router.post("/api/server/stop")
@router.post("/api/server/open-web")
```

- [ ] **Step 3: Register server router in `main.py`**

Add:
```python
from backend.app.routes.server import router as server_router
app.include_router(server_router)
```

- [ ] **Step 4: Run focused backend tests**

Run:
```powershell
python -m unittest tests.backend.test_server_service tests.backend.test_platform_services
```

Expected: PASS

- [ ] **Step 5: Commit API route wiring**

```bash
git add C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\server.py C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\main.py
git commit -m "feat: add server lifecycle api routes"
```

## Task 5: Add frontend types and API helpers

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts`

- [ ] **Step 1: Write failing frontend smoke assertions for server UI terms**

Extend smoke test to require:
- `Start server`
- `Stop server`
- `Run llama.cpp web`
- `Poslednja poruka`
- `PID`

- [ ] **Step 2: Run smoke test to verify failure**

Run:
```powershell
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: FAIL because strings are not yet present.

- [ ] **Step 3: Add `ServerStatusPayload` to `types.ts`**

Include fields:
- `status`
- `health`
- `port`
- `pid`
- `activeRuntime`
- `message`
- `localUrl`
- `tailscaleUrl`
- `canOpenWeb`

- [ ] **Step 4: Add API helpers to `api.ts`**

Implement:
```typescript
fetchServerStatus()
startServer()
stopServer()
openServerWeb()
```

- [ ] **Step 5: Re-run smoke test (should still fail on missing UI)**

Run:
```powershell
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: still FAIL until Home page is updated.

## Task 6: Add server block to Home page

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\HomePage.tsx`
- Modify if needed: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\components\StatusCard.tsx`

- [ ] **Step 1: Load server status on page load**

Add `fetchServerStatus()` alongside other Home data loading.

- [ ] **Step 2: Add `Server` status card/block**

Display:
- `Status`
- `Port`
- `Health`
- `PID`
- `Aktivni runtime`
- `Poslednja poruka`

- [ ] **Step 3: Add server actions**

Add buttons:
- `Start server`
- `Stop server`
- `Run llama.cpp web`

Each action should:
- set result panel payload
- refresh server state after completion

- [ ] **Step 4: Add URL display when available**

Show:
- local URL
- tailscale URL if present

- [ ] **Step 5: Make the block resilient to partial missing state**

Avoid dead `--` everywhere when message data exists.
Prefer readable fallback text.

- [ ] **Step 6: Run frontend smoke tests**

Run:
```powershell
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 7: Build frontend**

Run:
```powershell
& "C:\Users\AzdahaI9\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" ".\node_modules\vite\bin\vite.js" build
```

Workdir:
```text
C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend
```

Expected: build succeeds with new bundle.

- [ ] **Step 8: Commit Home server block**

```bash
git add C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\HomePage.tsx C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py
git commit -m "feat: add server control home panel"
```

## Task 7: End-to-end local verification

**Files:**
- No new files expected

- [ ] **Step 1: Run combined verification suite**

Run:
```powershell
python -m unittest tests.backend.test_server_service tests.backend.test_platform_services tests.frontend.test_ui_source_smoke tests.backend.test_opencode_service tests.backend.test_models_service
```

Expected: PASS

- [ ] **Step 2: Restart local backend**

Use the existing local startup method for `uvicorn` on `127.0.0.1:3210`.

- [ ] **Step 3: Verify API endpoints manually**

Check:
```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3210/api/server/status
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3210/api/health
```

Expected: valid JSON payloads.

- [ ] **Step 4: Verify UI in browser**

Confirm on `Home`:
- server block visible
- start/stop/web buttons visible
- status fields visible

- [ ] **Step 5: Exercise one safe path**

At minimum verify:
- `Run llama.cpp web` returns meaningful result
- `Start server` and `Stop server` produce meaningful status changes or explanations

- [ ] **Step 6: Commit verification-only adjustments if needed**

```bash
git add -A
git commit -m "test: verify server control parity flow"
```

Only if verification required code changes.

## Task 8: Windows/Linux parity pass

**Files:**
- Modify as needed:
  - `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py`
  - `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\script_runner.py`

- [ ] **Step 1: Check that both OS script names are explicitly mapped**

Verify the service calls exact Windows and Linux entrypoints, not Windows-only behavior.

- [ ] **Step 2: Add/extend tests for Linux mapping if missing**

Use env override:
```python
with mock.patch.dict("os.environ", {"CONTROL_CENTER_NEXT_TARGET_PLATFORM": "linux"}, clear=False):
```

- [ ] **Step 3: Run backend parity tests**

Run:
```powershell
python -m unittest tests.backend.test_server_service tests.backend.test_platform_services
```

Expected: PASS

- [ ] **Step 4: Commit parity cleanup**

```bash
git add C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\server_service.py C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_server_service.py
git commit -m "refactor: align server control api across windows and linux"
```

## Notes

- Reuse stable lifecycle logic whenever possible.
- Do not start benchmark work in this phase.
- Do not mix this with unrelated diagnostics or update UX changes.
- If a stable launcher is missing an equivalent `open web` command on one OS, surface that clearly instead of faking success.

## Plan Review Note

Formal plan-review subagent loop was not run in this session because explicit subagent delegation was not unlocked for this step. The plan is still written to be executable task-by-task with TDD and verification checkpoints.
