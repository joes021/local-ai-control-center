# Home / Server / OpenCode UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Home` more compact, add a dedicated `OpenCode` tab, and clarify the distinction between Control Center health and server health in the shared Windows/Linux Web UI.

**Architecture:** Keep the existing card-based dashboard, but reduce `Home` to summary-only cards and move OpenCode details into a dedicated tab. Reuse the existing shared backend payloads where possible, extending only the OpenCode status service if process/session visibility is available from the host system.

**Tech Stack:** React 19, TypeScript, Vite, FastAPI, Python backend services, Windows/Linux launcher adapters, unittest frontend/backend smoke coverage.

---

## File Map

**Frontend**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/App.tsx`
  - Add `OpenCode` tab between `Server` and `Models`.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/HomePage.tsx`
  - Remove `Version` and `Access mode` cards.
  - Rename `Health` to `Control Center health`.
  - Keep only compact `Server` and `OpenCode` summaries.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/ServerPage.tsx`
  - Keep detailed server health terminology here.
- Create or modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/OpenCodePage.tsx`
  - Full OpenCode status, settings, availability, instance count, optional process list.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/api.ts`
  - Add any missing OpenCode detail fetches if needed.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/types.ts`
  - Add OpenCode summary/detail fields for active state, instance count, optional process list.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/styles.css`
  - Compress `Home` cards, add compact warning badge styling, style OpenCode tab layout.

**Backend**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/opencode_service.py`
  - Return OpenCode active state and instance count, plus process list if reliable.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/routes/opencode.py`
  - Expose expanded OpenCode status payload.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/server_service.py`
  - Ensure compact warning text/source is available for Home summary.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/local_qwen_state.py`
  - Reuse/normalize runtime and server health terms if needed for consistent UI wording.

**Tests**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/frontend/test_ui_source_smoke.py`
  - Assert new `OpenCode` tab, renamed `Control Center health`, and removed `Version` / `Access mode` cards on Home.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_opencode_service.py`
  - Assert OpenCode status includes active state / instance count / optional process list behavior.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_server_service.py`
  - Assert summary warning fields when degraded.

---

### Task 1: Lock the UX contract with failing smoke tests

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/frontend/test_ui_source_smoke.py`

- [ ] **Step 1: Write failing frontend expectations**

Add assertions for:
- `OpenCode` tab existing in `App.tsx`
- `Control Center health` appearing on `Home`
- absence of `Version` and `Access mode` labels on `Home`
- compact OpenCode summary wording on `Home`

- [ ] **Step 2: Run smoke tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.frontend.test_ui_source_smoke
```

Expected:
- FAIL because `OpenCode` tab and renamed/removed Home content are not yet implemented.

- [ ] **Step 3: Commit test-only change**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add tests/frontend/test_ui_source_smoke.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "test: define home and opencode ux expectations"
```

---

### Task 2: Expand OpenCode backend status

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/opencode_service.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/routes/opencode.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_opencode_service.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/types.ts`

- [ ] **Step 1: Write failing backend tests for OpenCode detail payload**

Add tests for:
- `available / unavailable`
- `active`
- `instanceCount`
- optional `instances` list when detectable

- [ ] **Step 2: Run targeted backend tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_opencode_service
```

Expected:
- FAIL because payload fields do not exist yet.

- [ ] **Step 3: Implement OpenCode instance/status discovery**

Implementation notes:
- detect active OpenCode processes using existing platform helpers where possible
- return:
  - `available`
  - `active`
  - `instanceCount`
  - `instances` (only if reliable)
- do not invent unreliable session metadata

- [ ] **Step 4: Run backend OpenCode tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_opencode_service
```

Expected:
- PASS

- [ ] **Step 5: Commit OpenCode backend contract**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add backend/app/services/opencode_service.py backend/app/routes/opencode.py frontend/src/lib/types.ts tests/backend/test_opencode_service.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: expand opencode status payload"
```

---

### Task 3: Redesign Home into compact summary cards

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/HomePage.tsx`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/styles.css`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/types.ts`

- [ ] **Step 1: Implement the Home summary layout**

Make these UI changes:
- remove `Version` card
- remove `Access mode` card
- rename `Health` to `Control Center health`
- compact `Server` summary card:
  - status
  - port
  - runtime
  - health
  - warning badge
- compact `OpenCode` summary card:
  - available/unavailable/active
  - instance count when present
  - `Open OpenCode` button

- [ ] **Step 2: Add compact card styling**

In `styles.css`:
- reduce tall card content on Home
- add warning badge style
- keep card grid but make summary cards shallower

- [ ] **Step 3: Run frontend smoke tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.frontend.test_ui_source_smoke
```

Expected:
- PASS

- [ ] **Step 4: Commit Home redesign**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add frontend/src/pages/HomePage.tsx frontend/src/styles.css tests/frontend/test_ui_source_smoke.py frontend/src/lib/types.ts
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: compact home summary cards"
```

---

### Task 4: Add dedicated OpenCode tab

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/App.tsx`
- Create or modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/OpenCodePage.tsx`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/api.ts`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/styles.css`

- [ ] **Step 1: Add the tab to navigation**

Insert:
- `OpenCode`

Placement:
- after `Server`
- before `Models`

- [ ] **Step 2: Implement OpenCodePage**

Render:
- availability
- active state
- instance count
- optional process list
- executable/config path
- security mode
- capability mode
- action buttons
- session note that model changes apply only to future OpenCode sessions

- [ ] **Step 3: Run smoke tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.frontend.test_ui_source_smoke
```

Expected:
- PASS

- [ ] **Step 4: Commit OpenCode tab**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add frontend/src/App.tsx frontend/src/pages/OpenCodePage.tsx frontend/src/lib/api.ts frontend/src/styles.css
git -C 'C:\Users\\AzdahaI9\\Documents\\local-qwen-control-center-next' commit -m "feat: add dedicated opencode tab"
```

---

### Task 5: Clarify server wording and warning source

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/server_service.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_server_service.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/ServerPage.tsx`

- [ ] **Step 1: Write/extend failing server summary tests**

Add assertions that:
- degraded state yields warning text for Home summary
- server details keep `Server health` terminology

- [ ] **Step 2: Run targeted server tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_server_service
```

Expected:
- FAIL if warning normalization is missing.

- [ ] **Step 3: Implement server warning summary**

Expose concise summary warning fields for Home without duplicating all server detail prose.

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_server_service
```

Expected:
- PASS

- [ ] **Step 5: Commit server wording cleanup**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add backend/app/services/server_service.py tests/backend/test_server_service.py frontend/src/pages/ServerPage.tsx
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: clarify server health and warning summaries"
```

---

### Task 6: Full verification, version bump, and live rebuild

**Files:**
- Modify if needed: `C:/Users/AzdahaI9/Documents/Local Qwen 3.635Ba3B on home computer/version.json`
- Modify if needed: `C:/Users/AzdahaI9/LocalQwenHome/version.json`
- Modify if needed: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/package.json`
- Modify if needed: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/package-lock.json`

- [ ] **Step 1: Bump version according to user rule**

If this phase adds new user-visible feature scope, increment version appropriately before final build.

- [ ] **Step 2: Run focused backend and frontend tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.frontend.test_ui_source_smoke tests.backend.test_opencode_service tests.backend.test_server_service
```

Expected:
- PASS

- [ ] **Step 3: Run frontend build**

Run:

```powershell
$env:PATH = 'C:\Program Files\nodejs;' + $env:PATH
& 'C:\Program Files\nodejs\node.exe' '.\node_modules\typescript\bin\tsc' -b
& 'C:\Program Files\nodejs\node.exe' '.\node_modules\vite\bin\vite.js' build
```

Expected:
- TypeScript build passes
- Vite build emits new JS/CSS bundle

- [ ] **Step 4: Restart live UI and verify**

Run:

```powershell
$listener = Get-NetTCPConnection -LocalPort 3210 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess
if ($listener) { Stop-Process -Id $listener -Force }
Start-Sleep -Seconds 2
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\launchers\windows\start-control-center-next.ps1'
Start-Sleep -Seconds 6
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:3210/api/status').Content
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:3210/').Content
```

Expected:
- API returns healthy payload
- root references the new frontend bundle
- visible UI now uses the compact Home + dedicated OpenCode tab structure

- [ ] **Step 5: Commit final UX pass**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add .
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: redesign home and add opencode tab"
```
