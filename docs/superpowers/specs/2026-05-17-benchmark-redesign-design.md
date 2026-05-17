# Benchmark Redesign Design

Date: 2026-05-17
Project: `local-qwen-control-center-next`
Scope: Windows and Linux parity for the `Benchmark` tab in the shared Web UI

## Summary

The current `Benchmark` tab is useful as a read-only throughput snapshot, but it is still missing the behavior and clarity needed for a real benchmarking workflow. The redesign turns it into a persistent, actionable benchmark surface with:

- default benchmark scenarios
- editable custom test batteries
- `Run selected test`
- `Run full battery`
- persistent local history
- live progress while a benchmark is running
- time-based charting
- stable refresh behavior without blinking or resetting
- visible request activity with last 30 lines preview and full log access

This is a shared Web UI feature. The same frontend and API contract must work on both Windows and Linux, with only the execution adapters differing below the backend service layer.

## Goals

- Make benchmark execution obvious and interactive, not passive.
- Show live throughput immediately after benchmark start.
- Support both a quick single-test run and a full battery run.
- Preserve historical runs so the user can compare model/runtime/preset changes over time.
- Remove confusing helper prose and replace it with real chart axes and labels.
- Keep the UI stable during refreshes, without flicker or loss of already rendered data.

## Non-Goals

- Full statistical comparison dashboards across arbitrary historical groups in this phase.
- Cloud sync or remote benchmark history.
- Benchmark orchestration outside the local machine.

## User Experience

### Benchmark Tab Structure

The `Benchmark` tab is organized into five areas:

1. Benchmark controls
2. Run progress
3. Live metrics and chart
4. Request activity and live log preview
5. Benchmark history

### Benchmark Controls

The top of the tab provides:

- scenario selector
- `Run selected test`
- `Run full battery`
- `Save battery`
- `Load battery`
- `Restore default tests`

There are standard default scenarios shipped with the app. The user may edit them, save custom batteries, load a named battery later, and restore defaults at any time.

### Default Benchmark Scenarios

The app ships with a standard default battery. Initial recommended defaults:

- `short`
- `medium`
- `long`
- `code`

These defaults are editable, but `Restore default tests` always returns the original shipped set.

### Run Modes

Two benchmark execution modes are supported:

- `Run selected test`
- `Run full battery`

`Run full battery` is the primary workflow and should be emphasized in the UI. `Run selected test` is the quick local check workflow.

### Run Progress

When a battery is running, the UI shows:

- overall progress
- current scenario name
- run position such as `test 2/5`
- percent complete for the full battery

Below that, the full scenario list is shown with per-scenario status:

- `queued`
- `running`
- `done`
- `failed`

Scenario results remain visible after completion. They do not disappear automatically.

### Chart Behavior

The current helper sentences:

- `Y osa: tok/s`
- `X osa: skoriji zahtevi sleva nadesno`

must be removed from the rendered UI.

Instead:

- the X axis must show actual measurement time labels
- the Y axis is expressed through tick labels and grid lines
- chart refresh occurs every 5 seconds
- refresh must be lazy/stable, without clearing old data first
- the rendered chart should update data series in place instead of visually blinking

### Chart Legend

The legend remains vertical and should use real colored markers, not color words as text.

Planned series:

- input tok/s
- output tok/s
- ukupno tok/s

### Live Metrics

Immediately after clicking a benchmark action, the UI must start reflecting live throughput changes as new data arrives.

The UI must not wait until the entire benchmark finishes before showing useful signal.

### Request Activity

The `Request activity` section should:

- always show the latest available preview
- display the last 30 lines by default
- allow opening the full live log on click

The last benchmark-related activity should be visible without extra interaction.

### History

Benchmark history must persist locally across app restarts.

Each stored run records at minimum:

- date/time
- model
- runtime
- benchmark mode (`selected` or `full battery`)
- battery/scenario name
- key throughput metrics
- key latency metrics
- completion status

The history view should let the user review prior runs in the current phase. Rich comparison tooling can come later.

## Data Model

### Benchmark Scenario

Each scenario should include:

- stable id
- display name
- prompt body
- optional description
- optional tags such as `default`, `code`, `long`

### Benchmark Battery

Each battery should include:

- stable id
- display name
- ordered scenario ids
- source: `default` or `custom`
- timestamps for create/update

### Benchmark Run

Each run should include:

- stable run id
- mode: `selected` or `battery`
- battery id or scenario id
- model id
- runtime id
- access to active tuning context when relevant
- start time
- end time
- overall status
- per-scenario status list
- collected metrics samples
- summary result payload

## Backend Contract

The shared backend contract should expose benchmark state through dedicated routes rather than relying only on passive history reads.

Initial target endpoints:

- `GET /api/benchmark`
  - current snapshot, live metrics, chart data, preview log, summary activity, history summary
- `POST /api/benchmark/run-selected`
  - start a single selected scenario
- `POST /api/benchmark/run-battery`
  - start a full battery
- `GET /api/benchmark/run-status`
  - current active run state, progress, per-scenario status
- `POST /api/benchmark/batteries/save`
  - save custom battery
- `GET /api/benchmark/batteries`
  - list default and custom batteries
- `POST /api/benchmark/batteries/load`
  - load selected battery into editor
- `POST /api/benchmark/batteries/restore-defaults`
  - reset working battery to shipped defaults
- `GET /api/benchmark/history`
  - persistent historical runs

The backend must keep the API shared across Windows and Linux. Platform-specific differences belong only in the benchmark execution adapters.

## Execution Model

Benchmarks should run as background jobs, not block the request until completion.

Expected behavior:

- start route returns immediately with accepted run metadata
- frontend polls live run status
- metrics are appended as samples during execution
- chart and request activity update incrementally
- run completes into history automatically

## Error Handling

The UI should clearly distinguish:

- `queued`
- `running`
- `done`
- `failed`

Failure on one scenario must not make the whole run unreadable. The battery result should preserve:

- which scenario failed
- what succeeded
- the most useful error message available

If no benchmark data is yet available, the UI should say so clearly, without pretending that a chart is live.

## Persistence

Local persistence should include:

- custom batteries
- benchmark run history
- last known active benchmark snapshot if useful for continuity

Persistence should be stored under the same local app state conventions already used by the project, so Windows and Linux remain behaviorally aligned.

## Testing

This feature requires test coverage at three levels:

- backend service tests for scenario/battery/history/run-state behavior
- route tests for benchmark endpoints
- frontend tests for benchmark source rendering and text/controls presence

Critical test expectations:

- helper sentences about axes are no longer rendered
- chart axis labeling is based on data, not static prose
- run status supports per-scenario state progression
- default batteries can be restored
- history persists and is returned in API payloads

## Recommendation

Implement the redesign in two implementation slices:

1. Benchmark execution model and persistent data
2. Benchmark UI rendering and interaction polish

This keeps the live state contract stable before the more visual chart and interaction improvements land.

## Notes

- This spec is intentionally scoped to benchmark parity and redesign only.
- `Server`, `Models`, `OpenCode`, and update flows are outside this spec unless needed as benchmark dependencies.
- I did not run the formal spec-review subagent loop here because this session has not explicitly authorized subagent review for this spec step.
