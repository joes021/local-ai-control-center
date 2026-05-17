# Windows Parity Phase 1: MTP Truth And OpenCode Design

## Goal

Close the biggest functionality gap between the old Windows control center and the new Web UI by doing two things first:

1. Make model `MTP` status come from real source truth instead of loose heuristics.
2. Restore the most important OpenCode workflows in the new Windows Web UI.

This phase intentionally comes before benchmark parity because OpenCode launch and configuration are more important for daily use than charts.

## Scope

This phase covers:

- correct `MTP` labeling for models, especially Unsloth Qwen 3.6 models
- OpenCode launch from the new Web UI
- OpenCode configuration visibility in the new Web UI
- OpenCode settings editing in the new Web UI

This phase does **not** yet cover:

- benchmark chart parity
- throughput history panels
- full old benchmark tab migration

## Part 1: MTP Source Truth

### Problem

The current Web UI MTP labels were introduced as a metadata/filter improvement, but they are still too heuristic.

For Unsloth specifically, we now know there are separate repo lines for:

- non-MTP GGUF
- MTP GGUF

Examples:

- `unsloth/Qwen3.6-35B-A3B-GGUF`
- `unsloth/Qwen3.6-35B-A3B-MTP-GGUF`
- `unsloth/Qwen3.6-27B-GGUF`
- `unsloth/Qwen3.6-27B-MTP-GGUF`

### Required Behavior

`MTP status` should be derived from explicit source truth whenever possible.

Priority order:

1. explicit repo classification
2. explicit metadata field
3. filename/repo hint fallback
4. `unknown`

### User-Facing Result

Each model should still show:

- `MTP status: bez MTP`
- `MTP status: ima MTP`
- `MTP status: nepoznato`

But now Unsloth entries should be driven by their real repo family, not guesswork.

## Part 2: OpenCode Parity

### Problem

The new Windows Web UI currently lacks several important flows that the old Windows UI already had:

- OpenCode launch
- OpenCode availability/status
- OpenCode config visibility
- OpenCode-related settings control

That makes the new UI feel incomplete as a real Windows control center.

### Required Behavior

The new Web UI should regain OpenCode parity in a practical, daily-use-first way.

### Home Page Additions

Add a clear OpenCode section showing:

- whether OpenCode executable is available
- whether OpenCode config exists
- path to config directory or config file
- a direct `Open OpenCode` action

### Settings Page Additions

Expose the core OpenCode settings that already exist in the stable Windows scripts/state:

- working directory
- build steps
- plan steps
- general steps
- explore steps
- security mode
- capability mode

If current backend support already has additional stable OpenCode-related flags such as web access, those may be included too, but the goal is not to invent new settings. The goal is to surface existing ones from the old Windows system.

### Launch Behavior

The new UI should not fake OpenCode launch.

It should use the real Windows launcher path already present in the stable tooling, so clicking `Open OpenCode` performs the same real action the old Windows UI did.

### Error Handling

If OpenCode is not available:

- show `nije dostupan`
- show a short reason when possible
- do not silently fail

If config is missing:

- show `nema config`
- provide a clear action path via repair/config update if already supported

## Backend Shape

The new backend should expose an OpenCode status payload that includes at least:

- executable availability
- config availability
- config path
- working directory
- current step values
- security mode
- capability mode

It should also expose:

- an action route for `Open OpenCode`
- an apply route for OpenCode-related settings

## UI Priorities

This phase is not about visual redesign.

It is about restoring missing capability and making the new Windows Web UI truly usable as a control center.

Priority order:

1. correctness
2. visible status
3. working action buttons
4. clarity of settings
5. polish

## Success Criteria

This phase is successful when:

1. Unsloth models show correct `MTP` status based on real repo family.
2. The Web UI can visibly tell whether OpenCode is available.
3. The user can launch OpenCode from the new Web UI.
4. The user can see and edit the main OpenCode runtime/agent settings that existed in the old Windows UI.
5. No old-style Windows capability is silently missing once it belongs to this phase.
