# Model MTP Status Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add visible MTP status metadata to model cards and add three cross-group model filters: `Bez MTP`, `Ima MTP`, and `Nepoznato MTP`.

**Architecture:** Extend backend model normalization so every model entry exposes a normalized MTP status plus a Serbian label. Then update the frontend model types, filter state, and model rendering so cards display the status and the `Models` page can filter across all groups by MTP category.

**Tech Stack:** Python backend services, FastAPI routes, React + TypeScript frontend, Python `unittest`, Vite build.

---

## File Structure

- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\models_service.py`
  - Add MTP classification helpers and include MTP metadata in normalized model entries.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`
  - Add `mtpStatus` and `mtpStatusLabel` to `ModelEntry`.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\ModelsPage.tsx`
  - Render the new MTP status and add the three new filters.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_models_service.py`
  - Add backend tests for MTP classification.
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`
  - Add smoke assertions for the new filter labels and MTP status rendering.

## Task 1: Add backend MTP metadata classification

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\models_service.py`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\backend\test_models_service.py`

- [ ] **Step 1: Write the failing backend tests**

Add tests that verify:
- Unsloth non-MTP models resolve to `no-mtp`
- MTP models resolve to `has-mtp`
- unknown local/HF models resolve to `unknown`

Suggested test shapes:

```python
def test_unsloth_non_mtp_model_is_classified_as_no_mtp(self):
    from backend.app.services import models_service

    status = models_service._classify_mtp_status(
        source="unsloth",
        model_id="unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
        filename="Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
        raw={"source": "unsloth/Qwen3.6-35B-A3B-GGUF"},
    )

    self.assertEqual(status, "no-mtp")
```

```python
def test_mtp_variant_is_classified_as_has_mtp(self):
    from backend.app.services import models_service

    status = models_service._classify_mtp_status(
        source="unsloth",
        model_id="unsloth-Qwen3.6-35B-A3B-MTP.gguf",
        filename="Qwen3.6-35B-A3B-MTP.gguf",
        raw={"source": "unsloth/Qwen3.6-35B-A3B-MTP-GGUF"},
    )

    self.assertEqual(status, "has-mtp")
```

```python
def test_unknown_custom_model_is_classified_as_unknown(self):
    from backend.app.services import models_service

    status = models_service._classify_mtp_status(
        source="local",
        model_id="local-demo.gguf",
        filename="demo.gguf",
        raw={},
    )

    self.assertEqual(status, "unknown")
```

- [ ] **Step 2: Run the backend tests to confirm they fail**

Run:

```bash
python -m unittest tests.backend.test_models_service
```

Expected: FAIL because `_classify_mtp_status` and/or related MTP metadata are not implemented yet.

- [ ] **Step 3: Implement minimal backend MTP classification**

In `models_service.py`:
- Add `_classify_mtp_status(...) -> str`
- Add `_get_mtp_status_label(...) -> str`
- Use signal order:
  1. explicit metadata field if present
  2. known source/repo naming
  3. filename hint
  4. fallback `unknown`

Recommended minimal implementation pattern:

```python
def _classify_mtp_status(*, source: str, model_id: str, filename: str, raw: dict[str, object]) -> str:
    explicit = str(raw.get("mtpStatus", "") or "").strip().lower()
    if explicit in {"no-mtp", "has-mtp", "unknown"}:
        return explicit

    joined = " ".join(
        [
            source or "",
            model_id or "",
            filename or "",
            str(raw.get("source", "") or ""),
            str(raw.get("description", "") or ""),
        ]
    ).lower()

    if "mtp-gguf" in joined or "-mtp" in joined or " mtp" in joined:
        return "has-mtp"

    if source == "unsloth" and "mtp-gguf" not in joined:
        return "no-mtp"

    return "unknown"
```

Then extend `_build_model_entry(...)` so it adds:

```python
"mtpStatus": mtp_status,
"mtpStatusLabel": _get_mtp_status_label(mtp_status),
```

- [ ] **Step 4: Run backend tests again**

Run:

```bash
python -m unittest tests.backend.test_models_service
```

Expected: PASS

- [ ] **Step 5: Commit backend MTP classification**

```bash
git add backend/app/services/models_service.py tests/backend/test_models_service.py
git commit -m "feat: add model mtp status classification"
```

## Task 2: Add frontend model type support for MTP metadata

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\lib\types.ts`

- [ ] **Step 1: Add the new fields to `ModelEntry`**

Add:

```ts
mtpStatus?: "no-mtp" | "has-mtp" | "unknown";
mtpStatusLabel?: string;
```

- [ ] **Step 2: Run TypeScript build to catch type errors**

Run:

```bash
node .\node_modules\typescript\bin\tsc -b
```

Expected: PASS or fail only because UI usage has not been updated yet.

- [ ] **Step 3: Commit the type update**

```bash
git add frontend/src/lib/types.ts
git commit -m "feat: add mtp fields to model entry type"
```

## Task 3: Show MTP status on model cards

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\ModelsPage.tsx`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`

- [ ] **Step 1: Write/update the failing frontend smoke assertions**

Add assertions for strings such as:

```python
self.assertIn("MTP status", source)
self.assertIn("bez MTP", source)
self.assertIn("ima MTP", source)
self.assertIn("nepoznato", source)
```

- [ ] **Step 2: Run frontend smoke tests to confirm failure**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: FAIL because the strings are not yet rendered.

- [ ] **Step 3: Render MTP status on cards**

In both:
- `FilterResultsCard`
- `ModelGroup`

Add a helper line:

```tsx
<div className="helper-text">
  MTP status: {item.mtpStatusLabel ?? "nepoznato"}
</div>
```

Place it near other metadata lines like size/GPU/RAM.

- [ ] **Step 4: Run frontend smoke tests again**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 5: Commit card rendering changes**

```bash
git add frontend/src/pages/ModelsPage.tsx tests/frontend/test_ui_source_smoke.py
git commit -m "feat: show mtp status on model cards"
```

## Task 4: Add MTP filters to the Models page

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\src\pages\ModelsPage.tsx`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\frontend\test_ui_source_smoke.py`

- [ ] **Step 1: Extend filter state**

Change:

```ts
type ModelsFilter = "all" | "installed" | "active";
```

to:

```ts
type ModelsFilter =
  | "all"
  | "installed"
  | "active"
  | "no-mtp"
  | "has-mtp"
  | "unknown-mtp";
```

- [ ] **Step 2: Update filter matching logic**

Extend `matchesFilter(item)`:

```ts
if (modelsFilter === "no-mtp") {
  return item.mtpStatus === "no-mtp";
}
if (modelsFilter === "has-mtp") {
  return item.mtpStatus === "has-mtp";
}
if (modelsFilter === "unknown-mtp") {
  return item.mtpStatus === "unknown";
}
```

- [ ] **Step 3: Add the three new filter buttons**

Add buttons:

```tsx
<button ... onClick={() => setModelsFilter("no-mtp")}>Bez MTP</button>
<button ... onClick={() => setModelsFilter("has-mtp")}>Ima MTP</button>
<button ... onClick={() => setModelsFilter("unknown-mtp")}>Nepoznato MTP</button>
```

- [ ] **Step 4: Update `Rezultati filtera` heading label**

So the heading reflects the chosen MTP filter, for example:

```ts
filter === "no-mtp"
  ? "Modeli bez MTP"
  : filter === "has-mtp"
    ? "Modeli sa MTP"
    : filter === "unknown-mtp"
      ? "Modeli sa nepoznatim MTP statusom"
```

- [ ] **Step 5: Add smoke assertions for the new filter labels**

Add checks for:

```python
self.assertIn("Bez MTP", source)
self.assertIn("Ima MTP", source)
self.assertIn("Nepoznato MTP", source)
```

- [ ] **Step 6: Run frontend smoke tests**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 7: Build the frontend**

Run:

```bash
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

Expected: PASS

- [ ] **Step 8: Commit the filter changes**

```bash
git add frontend/src/pages/ModelsPage.tsx tests/frontend/test_ui_source_smoke.py
git commit -m "feat: add mtp filters to models page"
```

## Task 5: Final verification

**Files:**
- No new code files; verification only

- [ ] **Step 1: Run the focused test suite**

Run:

```bash
python -m unittest tests.backend.test_models_service tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 2: Run the broader local GUI suite**

Run:

```bash
python -m unittest tests.backend.test_models_service tests.backend.test_status_service tests.backend.test_platform_services tests.backend.test_script_runner tests.backend.test_settings_service tests.backend.test_native_dialogs tests.launchers.test_windows_launcher_smoke tests.frontend.test_ui_source_smoke
```

Expected: PASS

- [ ] **Step 3: Run production frontend build**

Run:

```bash
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

Expected: PASS

- [ ] **Step 4: Manual UI verification**

Verify in `Models`:
- cards show `MTP status`
- `Bez MTP` filter shows non-MTP Unsloth entries
- `Ima MTP` filter shows MTP entries if present
- `Nepoznato MTP` shows models without reliable metadata

- [ ] **Step 5: Commit final verification if needed**

```bash
git status
```

Expected: clean working tree after planned commits.

## Notes

- Do not block model actions based on MTP status.
- Keep the metadata conservative: if unsure, mark `unknown`.
- Follow existing UI style; do not redesign the page just to add these filters.
- If source metadata for more models becomes available later, prefer explicit fields over filename guessing.
