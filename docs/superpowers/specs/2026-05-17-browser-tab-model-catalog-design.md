# Browser Tab / Model Catalog Design

Date: 2026-05-17
Project: `local-qwen-control-center-next`
Scope: Shared Windows/Linux Web UI design for internet model browsing and compatibility entrypoint

## Summary

The application currently has a strong local `Models` management flow, but it lacks a true discovery surface for newly released models. Since new models appear frequently, users need a dedicated browser experience for remote catalogs without overloading the existing local-management tab.

This design introduces a new `Browser` tab for internet-discovered GGUF models relevant to `llama.cpp`. The first phase focuses on GGUF models from:

- `Hugging Face`
- `Unsloth`

The catalog uses a local cache by default, with explicit refresh actions from the internet. The browser provides:

- search
- filtering
- sorting
- a shared model table
- a detail side panel
- add/download actions
- a compatibility entrypoint

Compatibility is not calculated for all models at load time. Instead, the table shows the last known `Fit` result, while full compatibility calculation happens only when the user clicks `Check compatibility`.

The architecture should remain open for additional sources later, including `Ollama`, but the first visible UI phase is GGUF-only.

## Goals

- Let users discover newly available GGUF models from remote sources.
- Keep `Models` focused on local and installed content.
- Provide a fast browser experience by relying on local cache first.
- Support search, filtering, and sorting over a shared model list.
- Make model evaluation practical through a detail panel and compatibility entrypoint.
- Keep the data model extensible for future non-GGUF or other-source expansion.

## Non-Goals

- Full non-GGUF browsing in phase 1.
- Automatic compatibility calculation for the entire remote catalog at load time.
- Multi-hardware-profile compatibility comparison in phase 1.
- Embedded source-page preview in phase 1.

## Information Architecture

### Tab Split

The UI will separate local and remote concerns:

- `Models` = models already known locally, active, installed, or managed on-machine
- `Browser` = remote internet-discovered GGUF model catalog

This avoids overloading `Models` with both local lifecycle management and internet discovery.

### Source Model

The internal catalog architecture should be broader than the first UI. It must be able to represent at least:

- `Hugging Face`
- `Unsloth`
- `Ollama`

However, phase 1 UI visibility is limited to:

- `GGUF`
- `llama.cpp` relevant entries
- sources shown in UI:
  - `Hugging Face`
  - `Unsloth`

`Ollama` should be supported in the underlying data model, but not rendered in the first UI pass.

## Browser Tab Layout

The `Browser` tab is composed of three zones:

1. control bar
2. shared model table
3. detail side panel

### Control Bar

The top control area includes:

- `Search`
- `Refresh from internet`
- `Refresh Hugging Face`
- `Refresh Unsloth`
- cache freshness information
- refresh errors or warnings

Most users should use the global refresh button. Per-source refresh remains available as an advanced/debug action.

## Shared Model Table

The main view is a single shared table, not separate source tabs.

This is the recommended approach because users primarily care about:

- model
- quantization
- size
- fit

and not about the source as the primary grouping dimension.

Source is still visible and filterable, but it does not split the table into different screens.

### Table Columns

Phase 1 columns:

- `Model`
- `Family`
- `Source`
- `Quant`
- `Size`
- `Last update`
- `MTP`
- `Fit`

### Search

The browser supports search across:

- model name
- model family

### Required Filters

Phase 1 filter set:

- `source`
- `model family`
- `kvantizacija`
- `veličina`
- `MTP status`
- `datum`

### Sorting

The table supports sorting across relevant columns, especially:

- model
- size
- date
- source
- quantization

## Detail Side Panel

Selecting a row opens a detail side panel on the right.

This is preferred over row expansion because:

- the table remains stable
- the list height does not explode
- richer detail content fits better
- future compatibility output fits naturally here

### Detail Contents

The panel should show:

- model name
- family
- source
- GGUF filename
- quantization
- size
- published date, if available
- last update date
- MTP status
- description, when available
- source page link

### Detail Actions

The panel includes:

- `Download`
- `Add to local catalog`
- `Open source page`
- `Check compatibility`

## Add to Local Catalog Behavior

`Add to local catalog` does not automatically imply download.

The intended flow is:

1. add the model to the local catalog
2. immediately offer:
   - `Pokreni download odmah`
   - or `Ostavi samo u katalogu`

This avoids the prior confusion where “add” and “download” were easy to conflate.

## Open Source Page Behavior

Phase 1 behavior:

- open the original source page directly

Examples:

- source page on `Hugging Face`
- source page on `Unsloth`

An embedded internal preview is intentionally deferred.

## Cache Model

The browser operates from local cache by default.

Cache should store:

- basic model metadata
- last refresh timestamp
- model count by source
- last refresh errors/warnings
- last known `Fit` result

This makes the browser:

- fast
- stable
- usable even without constant live internet fetches

### Refresh Model

Supported refresh actions:

- `Refresh from internet`
- `Refresh Hugging Face`
- `Refresh Unsloth`

The global refresh is the main UX path. Per-source refresh is secondary but useful for diagnostics and partial failures.

## Date Handling

The browser should track both:

- publish date
- last update date

Presentation rules:

- main table date column = `last update`
- detail panel also shows:
  - `published`
  - `last update`

This gives the user both freshness and original-age context.

## MTP Status

The browser should surface:

- `bez MTP`
- `ima MTP`
- `nepoznato`

This should align with the earlier shared MTP metadata approach and use source truth where available.

## Fit / Compatibility Entry

### Table Fit Column

The table includes a `Fit` column with only the last known result:

- `radi`
- `granično`
- `ne radi`
- `nije provereno`

### Compatibility Calculation Trigger

Detailed compatibility is **not** computed for every model on page load.

Instead:

- detailed calculation happens only when the user clicks `Check compatibility`
- the result is then saved as the latest known `Fit` state

This is the preferred approach because it keeps the browser fast and avoids expensive catalog-wide calculations during normal browsing.

## Compatibility Scope in Phase 1

Phase 1 compatibility uses:

- the current local machine only

It should consider, as much as the available metadata allows:

- VRAM
- RAM
- context size
- output size
- quantization
- TurboQuant effects
- MoE implications

The architecture should remain ready for future support of:

- multiple saved hardware profiles

but that is not part of phase 1 UI behavior.

## Compatibility UX

`Check compatibility` should return a detailed explanation, not just a badge.

Expected output type:

- `radi`
- `granično`
- `verovatno ne radi`

plus reasoning, such as:

- VRAM fit
- RAM fit
- context pressure
- output pressure
- MoE effect
- TurboQuant impact

## Error Handling

The browser must make incomplete refreshes visible.

Examples:

- Hugging Face refresh failed, Unsloth succeeded
- cache is stale
- a source returned partial metadata only

This should appear in the refresh status area, not as silent failure.

## Verification

This design is complete only when:

- a new `Browser` tab exists
- it displays a single shared GGUF table
- search works on model name and family
- the six required filters are present
- sorting works
- the detail panel opens on row selection
- the detail panel exposes:
  - `Download`
  - `Add to local catalog`
  - `Open source page`
  - `Check compatibility`
- cache metadata includes:
  - model data
  - last refresh
  - per-source counts
  - last refresh errors/warnings
  - last known fit
- the table shows `Fit` from the last known result, not from eager global computation
- the first visible source set is GGUF models from:
  - `Hugging Face`
  - `Unsloth`
- the data model remains ready for `Ollama` later without forcing it into phase 1 UI
