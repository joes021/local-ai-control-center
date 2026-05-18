# Browser Tab / Model Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated `Browser` tab for remote GGUF model discovery with local cache, filtering, detail panel actions, and on-demand compatibility checks for the current machine.

**Architecture:** Keep `Models` focused on local assets and create a separate remote catalog flow under `Browser`. The backend owns source refresh, cache persistence, and compatibility calculations; the frontend renders a shared GGUF table with filters, search, sorting, and a right-side detail panel.

**Tech Stack:** React 19, TypeScript, Vite, FastAPI, Python services, local JSON cache/state, Windows/Linux shared UI contract, unittest-based backend/frontend verification.

---

## File Map

**Frontend**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/App.tsx`
  - Add `Browser` tab in navigation.
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/BrowserPage.tsx`
  - Main browser UI with search, filters, table, refresh controls, and detail panel.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/api.ts`
  - Add browser catalog, refresh, add/download, and compatibility APIs.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/types.ts`
  - Add browser model, cache, refresh, and compatibility payload types.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/styles.css`
  - Add browser table, side panel, filter bar, and cache status styling.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/frontend/test_ui_source_smoke.py`
  - Assert new Browser tab and core UI strings.

**Backend**
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/routes/browser.py`
  - Browser-specific endpoints.
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/browser_catalog_service.py`
  - Unified GGUF catalog, cache loading, refresh orchestration.
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/browser_sources.py`
  - Source adapters for Hugging Face and Unsloth, with Ollama-ready abstraction hidden in phase 1.
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/compatibility_service.py`
  - Detailed compatibility calculator for current local machine only.
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/main.py`
  - Register browser routes.
- Modify if needed: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/models_service.py`
  - Reuse local catalog add/download helpers if that is the cleanest boundary.
- Create tests:
  - `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_browser_catalog_service.py`
  - `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_browser_routes.py`
  - `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_compatibility_service.py`

**Cache / State**
- Create or use under `C:/Users/AzdahaI9/LocalQwenHome/state/`:
  - `browser-model-catalog.json`
  - `browser-refresh-status.json`
  - `browser-compatibility-cache.json`

---

### Task 1: Lock the Browser tab UX contract with failing smoke tests

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/frontend/test_ui_source_smoke.py`

- [ ] **Step 1: Write failing UI expectations**

Add assertions for:
- `Browser` tab in `App.tsx`
- `Search`
- `Refresh from internet`
- `Refresh Hugging Face`
- `Refresh Unsloth`
- `Fit`
- `Check compatibility`
- `Add to local catalog`

- [ ] **Step 2: Run smoke tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.frontend.test_ui_source_smoke
```

Expected:
- FAIL because Browser tab and strings do not yet exist.

- [ ] **Step 3: Commit the failing expectations**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add tests/frontend/test_ui_source_smoke.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "test: define browser tab ui expectations"
```

---

### Task 2: Build the backend catalog and local cache model

**Files:**
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/browser_catalog_service.py`
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/browser_sources.py`
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_browser_catalog_service.py`

- [ ] **Step 1: Write failing catalog/cache tests**

Cover:
- loading cached models
- refresh metadata storage:
  - last refresh
  - counts by source
  - last refresh errors/warnings
- GGUF-only filtering in phase 1 visible output
- hidden but supported source abstraction for future Ollama

- [ ] **Step 2: Run targeted backend tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_browser_catalog_service
```

Expected:
- FAIL because service does not exist yet.

- [ ] **Step 3: Implement shared catalog/cache layer**

Requirements:
- local cache first
- explicit refresh orchestration
- source normalization into a single GGUF model shape
- persisted refresh metadata

- [ ] **Step 4: Run catalog/cache tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_browser_catalog_service
```

Expected:
- PASS

- [ ] **Step 5: Commit backend catalog foundation**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add backend/app/services/browser_catalog_service.py backend/app/services/browser_sources.py tests/backend/test_browser_catalog_service.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: add browser catalog cache layer"
```

---

### Task 3: Add browser routes and actions

**Files:**
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/routes/browser.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/main.py`
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_browser_routes.py`
- Modify if needed: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/models_service.py`

- [ ] **Step 1: Write failing route tests**

Cover endpoints for:
- get cached browser catalog
- refresh all
- refresh Hugging Face
- refresh Unsloth
- add to local catalog
- open source page payload handoff

- [ ] **Step 2: Run targeted route tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_browser_routes
```

Expected:
- FAIL because routes do not exist yet.

- [ ] **Step 3: Implement browser route layer**

Notes:
- keep `Models` local management separate
- `Add to local catalog` should only add, then return enough signal for UI to offer immediate download
- do not auto-download silently

- [ ] **Step 4: Run route tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_browser_routes
```

Expected:
- PASS

- [ ] **Step 5: Commit browser routes**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add backend/app/routes/browser.py backend/app/main.py tests/backend/test_browser_routes.py backend/app/services/models_service.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: expose browser catalog endpoints"
```

---

### Task 4: Add detailed compatibility calculator

**Files:**
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/services/compatibility_service.py`
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/tests/backend/test_compatibility_service.py`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/backend/app/routes/browser.py`

- [ ] **Step 1: Write failing compatibility tests**

Cover:
- last known fit cache
- detailed result categories:
  - `radi`
  - `granicno`
  - `verovatno ne radi`
  - `nije provereno`
- reasoning fields for:
  - VRAM
  - RAM
  - context
  - output
  - quantization
  - TurboQuant effect
  - MoE effect where metadata exists

- [ ] **Step 2: Run compatibility tests to verify failure**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_compatibility_service
```

Expected:
- FAIL because service does not exist yet.

- [ ] **Step 3: Implement compatibility service**

Constraints:
- calculate only on explicit `Check compatibility`
- use current local machine only in phase 1
- persist last known `Fit` result in compatibility cache

- [ ] **Step 4: Run compatibility tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_compatibility_service
```

Expected:
- PASS

- [ ] **Step 5: Commit compatibility service**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add backend/app/services/compatibility_service.py tests/backend/test_compatibility_service.py backend/app/routes/browser.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: add browser compatibility calculator"
```

---

### Task 5: Build the Browser tab frontend

**Files:**
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/App.tsx`
- Create: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/pages/BrowserPage.tsx`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/api.ts`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/lib/types.ts`
- Modify: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/src/styles.css`

- [ ] **Step 1: Add the Browser tab shell**

Insert new tab:
- `Browser`

Place it in navigation without changing other tab responsibilities.

- [ ] **Step 2: Build BrowserPage**

Render:
- search box
- refresh buttons
- refresh status
- shared GGUF table
- filters
- sorting
- right-side detail panel

- [ ] **Step 3: Add detail actions**

Wire:
- `Download`
- `Add to local catalog`
- `Open source page`
- `Check compatibility`

Behavior:
- after `Add to local catalog`, UI must offer immediate download

- [ ] **Step 4: Run smoke tests**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.frontend.test_ui_source_smoke
```

Expected:
- PASS

- [ ] **Step 5: Commit browser UI**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add frontend/src/App.tsx frontend/src/pages/BrowserPage.tsx frontend/src/lib/api.ts frontend/src/lib/types.ts frontend/src/styles.css tests/frontend/test_ui_source_smoke.py
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: add browser tab ui"
```

---

### Task 6: Full verification, versioning, and live rebuild

**Files:**
- Modify if needed: `C:/Users/AzdahaI9/Documents/Local Qwen 3.635Ba3B on home computer/version.json`
- Modify if needed: `C:/Users/AzdahaI9/LocalQwenHome/version.json`
- Modify if needed: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/package.json`
- Modify if needed: `C:/Users/AzdahaI9/Documents/local-qwen-control-center-next/frontend/package-lock.json`

- [ ] **Step 1: Bump version according to user rule**

If Browser tab and compatibility are delivered, this is a feature-level increment of `b`, not just `c`.

- [ ] **Step 2: Run focused backend + frontend verification**

Run:

```powershell
& 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\.venv\Scripts\python.exe' -m unittest tests.backend.test_browser_catalog_service tests.backend.test_browser_routes tests.backend.test_compatibility_service tests.frontend.test_ui_source_smoke
```

Expected:
- PASS

- [ ] **Step 3: Build frontend**

Run:

```powershell
$env:PATH = 'C:\Program Files\nodejs;' + $env:PATH
& 'C:\Program Files\nodejs\node.exe' '.\node_modules\typescript\bin\tsc' -b
& 'C:\Program Files\nodejs\node.exe' '.\node_modules\vite\bin\vite.js' build
```

Expected:
- build succeeds
- new JS/CSS bundle generated

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
- healthy backend
- correct version
- Browser tab visible in live UI

- [ ] **Step 5: Commit final browser feature pass**

```powershell
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' add .
git -C 'C:\Users\AzdahaI9\Documents\local-qwen-control-center-next' commit -m "feat: add remote browser tab and compatibility flow"
```
