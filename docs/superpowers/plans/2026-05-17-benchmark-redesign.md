# Benchmark Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current passive benchmark view into a real benchmark workflow with runnable scenarios, full battery execution, live progress, time-based charting, and persistent local history.

**Architecture:** Add a benchmark run state layer and battery/history persistence in the backend, then extend the shared frontend to render controls, live progress, time labels, and history from the new API contract. Keep the Web UI shared for Windows and Linux; only benchmark execution adapters differ below the service layer.

**Tech Stack:** FastAPI backend, Python file-backed state, React + TypeScript frontend, unittest-based backend/frontend source smoke tests.

---

### Task 1: Extend benchmark backend contract

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\benchmark_service.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\benchmark.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_benchmark_service.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_benchmark_routes.py`

- [ ] Write failing tests for batteries, active run status, history, and axis-friendly time labels.
- [ ] Run backend benchmark tests and verify they fail for missing fields/routes.
- [ ] Implement minimal benchmark state helpers and route payloads.
- [ ] Re-run backend benchmark tests and verify they pass.

### Task 2: Add benchmark actions and persistence

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\benchmark_service.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\routes\benchmark.py`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`

- [ ] Add failing tests for `run-selected`, `run-battery`, `save battery`, `load battery`, `restore defaults`, and persisted history.
- [ ] Run route tests and verify failures.
- [ ] Implement minimal POST/GET endpoints and file-backed persistence.
- [ ] Re-run benchmark backend tests and verify they pass.

### Task 3: Redesign benchmark UI

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\BenchmarkPage.tsx`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\api.ts`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`

- [ ] Write failing frontend smoke assertions for missing controls and for removed helper-axis prose.
- [ ] Run frontend smoke test and verify failures.
- [ ] Implement benchmark controls, scenario status list, history section, and chart label cleanup.
- [ ] Re-run frontend smoke test and verify it passes.

### Task 4: Verification and version bump

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\version.json`
- Modify: `C:\Users\AzdahaI9\LocalQwenHome\version.json`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\package.json`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\package-lock.json`

- [ ] Bump feature version after implementation lands.
- [ ] Run benchmark backend tests.
- [ ] Run frontend smoke tests.
- [ ] Build frontend bundle.
- [ ] Verify live `http://127.0.0.1:3210/` shows the new benchmark controls and no longer shows the old helper-axis text.
