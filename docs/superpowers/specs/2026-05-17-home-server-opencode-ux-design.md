# Home / Server / OpenCode UX Design

Date: 2026-05-17
Project: `local-qwen-control-center-next`
Scope: Shared Windows/Linux Web UI polish for `Home`, new `OpenCode` tab, and clearer server state language

## Summary

The current `Home` screen is functional but still too tall, too repetitive, and not clear enough about the difference between Control Center state and `llama.cpp` server state. `OpenCode` is also important enough that it should no longer live only as a card on `Home`; it needs a dedicated tab.

This redesign keeps the existing card-based dashboard structure, but makes it more compact and clearer:

- keep `Home` as a summary dashboard
- remove the `Version` and `Access mode` cards from `Home`
- rename `Health` to `Control Center health`
- keep `Server` as a compact summary on `Home`
- add a dedicated `OpenCode` tab between `Server` and `Models`
- reduce large explanatory blocks on `Home`
- move detailed OpenCode state and configuration into the new `OpenCode` tab

The Web UI and API contract remain shared between Windows and Linux. Platform-specific differences stay below the backend service layer.

## Goals

- Make `Home` more compact without throwing away the current dashboard structure.
- Clarify the difference between Control Center health and `llama.cpp` server health.
- Give `OpenCode` a first-class place in navigation.
- Keep only summary-level information on `Home`.
- Move detailed status and settings into dedicated tabs.
- Preserve parity between Windows and Linux UI structure.

## Non-Goals

- Full redesign of the entire application layout in this phase.
- Removal of the existing `Server` tab.
- Adding unrelated benchmark, repair, or update features in this phase.

## Home Screen Design

### Keep the Card Layout

`Home` remains a card-based dashboard. This avoids a disruptive redesign while still allowing the screen to become much more compact.

Cards stay as the main presentation model, but content inside the cards is reduced to summary signals only.

### Remove Cards

The following cards are removed from `Home`:

- `Version`
- `Access mode`

Version remains visible directly in the application title, which is the cleaner and more important location for it.

Access mode is still available elsewhere in settings, but it is not important enough for the main dashboard and is currently confusing for the user.

### Rename Control Center Health

The current `Health` card is renamed to:

- `Control Center health`

This card refers to the health of the shared Web UI/backend itself, not to the `llama.cpp` model server.

This avoids confusion with `Server health`, which refers specifically to the runtime server.

### Server Summary Card on Home

`Home` keeps a compact `Server` summary card. It shows:

- server status
- server port
- active runtime
- server health
- warning badge when degraded or inconsistent

The warning appears only when there is something the user should notice, for example:

- lifecycle says active but health is missing
- runtime config is selected but process is not confirmed
- port exists but server is not healthy

The warning should be visually noticeable but compact, using a small badge or inline highlighted indicator rather than a large block.

### OpenCode Summary Card on Home

`Home` keeps only a compact OpenCode summary card. It shows:

- `dostupan` / `nedostupan` / `aktivan`
- instance count if it can be measured reliably
- a small `Open OpenCode` button

It must not contain the long explanatory and settings-heavy content that currently makes the screen tall.

## OpenCode Tab

### Navigation

Add a new tab:

- `OpenCode`

Placement:

- between `Server` and `Models`

This keeps the information architecture intuitive:

- `Home`
- `Server`
- `OpenCode`
- `Models`

### OpenCode Tab Contents

The `OpenCode` tab becomes the full operational surface for OpenCode. It contains:

- availability state
- active state
- instance count
- instance/process list if reliable and supported
- executable/config path details
- configuration summary
- security mode
- capability mode
- working directory and related settings
- action buttons such as `Open OpenCode`

If a reliable session/process list can be derived from the system, show it. If not, fall back to:

- availability
- active/inactive
- instance count

### OpenCode Session Behavior Note

Keep the existing clear rule:

- changing model in Control Center updates OpenCode configuration for the next OpenCode session
- it does not hot-swap an already open OpenCode session

This message should remain visible in the OpenCode area, but it belongs in the `OpenCode` tab more than on `Home`.

## Server Terminology

The UI must distinguish between two different health concepts:

- `Control Center health`
- `Server health`

Definitions:

- `Control Center health` = health of the shared local backend/Web UI
- `Server health` = health of the `llama.cpp` runtime server

`Home` shows only the first as its own card and includes the second only inside the compact `Server` summary card.

The dedicated `Server` tab remains the place for full server details, lifecycle state, PID, URLs, start/stop actions, and runtime server reasoning.

## Layout Compactness Rules

To reduce vertical sprawl on `Home`:

- cards should remain shallow summary cards
- long helper paragraphs should be removed from `Home`
- long explanations should move into dedicated tabs
- one-liner state summaries are preferred over stacked prose

This redesign should make `Home` feel like a dashboard again, not like a settings page split into tiles.

## Data / Backend Requirements

The backend must continue to provide enough signal for:

- Control Center health
- server lifecycle status
- server health
- active runtime
- OpenCode availability
- OpenCode active state
- OpenCode instance count
- OpenCode process list where possible

No new cross-platform architectural split is introduced here. The shared API remains the source of truth, with Windows/Linux specifics handled under the backend adapters.

## Verification

This redesign is complete only when all of the following are true:

- `Home` no longer shows `Version` and `Access mode` cards
- `Home` shows `Control Center health` instead of generic `Health`
- `Home` keeps a compact `Server` summary card with warning support
- `Home` keeps only a compact OpenCode summary card
- `OpenCode` exists as a separate tab between `Server` and `Models`
- detailed OpenCode content is moved out of `Home`
- the distinction between Control Center health and server health is clear in UI wording
- Windows and Linux continue to use the same Web UI structure
