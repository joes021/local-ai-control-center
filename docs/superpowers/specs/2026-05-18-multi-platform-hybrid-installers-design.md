# Multi-Platform Hybrid Installers Design

Date: 2026-05-18
Project: `local-qwen-control-center-next`
Scope: Public GitHub installers for Windows, Ubuntu x86_64, and Ubuntu arm64

## Summary

`Local AI Control Center` currently exists as a working codebase and launcher stack, but it does not yet ship as a complete, end-user-ready installer story across all target platforms. The current gap is most visible on `Ubuntu arm64`: the UI can be deployed, but the machine may still be missing the real runtime layer:

- `llama.cpp`
- `OpenCode`
- `TurboQuant`
- supporting dependencies such as `python3`, `venv`, `node`, and `npm`

That means the application may look installed while still being functionally incomplete.

This design introduces a **hybrid installer strategy** for three public GitHub release artifacts:

- `Windows`
- `Ubuntu x86_64`
- `Ubuntu arm64`

Each installer ships the application payload and installer scripts directly, but it also performs real setup work at install time:

- dependency checks
- dependency installation when needed
- runtime preparation
- service/bootstrap verification
- final success/failure reporting by subsystem

The goal is not merely to unpack files. The goal is to finish installation with a machine that is actually usable.

## Goals

- Publish three public GitHub installer artifacts:
  - Windows `.exe`
  - Ubuntu x86_64 `.run`
  - Ubuntu arm64 `.run`
- Ensure installation success is defined by functional readiness, not only file copy completion.
- Automatically prepare missing runtime dependencies during installation when reasonably possible.
- Make `llama.cpp` and `OpenCode` required success conditions.
- Treat `TurboQuant` as platform-aware and optional where support is not yet guaranteed.
- Produce installation results that clearly show which subsystems are ready and which are not.

## Non-Goals

- Fully offline or fat installers that embed all large binaries and packages.
- Perfectly identical runtime capabilities across every platform on day one.
- Automatic guarantee that `TurboQuant` is available on `Ubuntu arm64`.
- Full package-manager abstraction for every Linux distribution in phase 1.

## Recommended Installer Strategy

Three broad approaches were considered:

1. `Thin installer`
2. `Hybrid installer`
3. `Fat/offline installer`

The recommended approach is **Hybrid installer**.

### Why Hybrid Is Preferred

It provides the best balance between:

- installer size
- maintainability
- platform flexibility
- real post-install usability

It avoids both extremes:

- not merely a file-copy wrapper
- not a huge artifact that embeds every binary and library

Instead, the installer ships the application payload and the installation logic, then performs platform-specific setup work during installation.

## Target Artifacts

Each GitHub release should publish these primary installer artifacts:

- `Local-AI-Control-Center-Setup-<version>.exe`
- `Local-AI-Control-Center-Setup-linux-x86_64-<version>.run`
- `Local-AI-Control-Center-Setup-linux-arm64-<version>.run`

Supporting release files:

- `checksums.txt`
- `release-notes.txt`
- `support-matrix.json`

## Release Metadata

### checksums.txt

Must contain SHA256 checksums for all published installer artifacts.

### release-notes.txt

Must summarize:

- version
- major changes
- installer-specific notes if relevant

### support-matrix.json

Must describe current platform readiness for at least:

- `Control Center`
- `llama.cpp`
- `OpenCode`
- `TurboQuant`

This is especially important for `Ubuntu arm64`, where `TurboQuant` may remain optional or experimental.

## Payload Versus Deferred Installation

The installer should always carry the **application payload**, but not necessarily every external runtime dependency.

### Included in Installer Payload

Each installer should include:

- `Control Center Next` frontend source/build payload
- backend code
- launchers
- install scripts
- default profiles and config
- icons/assets
- release metadata

### Installed or Fetched During Setup

During installation, the installer should verify and, when possible, install or prepare:

- `python`
- `venv`
- `node`
- `npm`
- `OpenCode`
- `llama.cpp`
- model download or model selection
- `TurboQuant` when supported and requested

This keeps the release artifacts manageable while still making installation practically complete.

## Platform-Specific Installer Design

## Windows Installer

The Windows installer should continue using the existing `Inno Setup` outer packaging flow.

### Windows Flow

1. Install payload into target directory
2. Launch Windows bootstrap/install script
3. Verify or install dependencies
4. Verify or install `OpenCode`
5. Verify or install `llama.cpp`
6. Optionally download or verify a model
7. Prepare settings, state, launchers, and shortcuts
8. Optionally prepare `TurboQuant`
9. Run final verification
10. Produce final readiness report

### Windows Success Requirements

Required:

- `Control Center`
- `llama.cpp`
- `OpenCode`

Optional/platform-dependent:

- `TurboQuant`

## Ubuntu x86_64 Installer

The Ubuntu x86_64 installer should be a self-extracting `.run` package.

### Ubuntu x86_64 Flow

1. Extract payload into working directory
2. Run Linux installer script
3. Check/install package dependencies
4. Verify or install `python3`, `venv`, `node`, `npm`
5. Verify or install `OpenCode`
6. Clone/build or verify `llama.cpp`
7. Optionally download or verify a model
8. Prepare config, desktop entry, and launcher scripts
9. Optionally prepare `TurboQuant`
10. Run final verification and launch readiness report

### Ubuntu x86_64 Success Requirements

Required:

- `Control Center`
- `llama.cpp`
- `OpenCode`

Optional:

- `TurboQuant`

## Ubuntu arm64 Installer

The Ubuntu arm64 installer should also be a self-extracting `.run` package, but with stricter architecture-aware checks.

### Ubuntu arm64 Flow

1. Extract payload into working directory
2. Run Linux installer script
3. Check/install package dependencies
4. Verify or install `python3`, `venv`, `node`, `npm`
5. Verify or install `OpenCode`
6. Clone/build or verify `llama.cpp`
7. Optionally download or verify a model
8. Prepare config, desktop entry, and launcher scripts
9. Detect `TurboQuant` support and installation viability
10. Run final verification and launch readiness report

### Ubuntu arm64 Success Requirements

Required:

- `Control Center`
- `llama.cpp`
- `OpenCode`

Optional:

- `TurboQuant`

`TurboQuant` failure must not silently pass. It must be clearly reported as one of:

- `OK`
- `nije prisutan`
- `nije podržan`
- `instalacija nije uspela`

## Definition of Successful Installation

An installation is not considered successful merely because the installer completed without crashing.

### Minimum Success Criteria

Installation is `successful` only if all of the following are true:

- `Control Center: OK`
- `llama.cpp: OK`
- `OpenCode: OK`

### TurboQuant Handling

`TurboQuant` is a separate status line and may be:

- `OK`
- `nije prisutan`
- `nije podržan`
- `instalacija nije uspela`

For `Ubuntu arm64`, installation may still be considered successful if:

- `Control Center`, `llama.cpp`, and `OpenCode` are all `OK`
- `TurboQuant` is clearly marked as optional/unavailable rather than silently failing

## Failure and Fallback Behavior

### Hard Failure Conditions

The installer must fail the installation if any of these fail:

- `Control Center`
- `llama.cpp`
- `OpenCode`

### Soft Failure Conditions

The installer may finish with warning if:

- `TurboQuant` is unavailable
- `TurboQuant` is unsupported on the detected platform
- `TurboQuant` installation failed but the rest of the platform is usable

### User-Facing Result

The installer must always end with a subsystem report that includes:

- `Control Center`
- `llama.cpp`
- `OpenCode`
- `TurboQuant`
- install path
- launcher path
- local URL, if available
- Tailscale URL, if configured
- log file location

## Installer Progress Model

The installer should expose clear staged progress. Recommended stages:

- `priprema`
- `zavisnosti`
- `OpenCode`
- `llama.cpp`
- `model`
- `TurboQuant`
- `zavrsna provera`

This applies both to GUI-capable flows and CLI/TUI fallback flows.

## Runtime Validation After Install

The installer should finish by validating actual readiness, not just artifact presence.

Recommended post-install checks:

- can the backend start
- can the UI be served
- is `llama.cpp` executable resolvable
- is `OpenCode` executable resolvable
- is the configured runtime detected
- if `TurboQuant` is expected, is it actually detectable

## GitHub Release Presentation

Each release should clearly describe the three installers and their expected platform support.

Recommended release summary:

- `Windows`: full installer
- `Ubuntu x86_64`: full installer
- `Ubuntu arm64`: full installer, `TurboQuant` optional/experimental until fully confirmed

This keeps the release honest and reduces confusion for ARM users.

## Reuse of Existing Assets

The current codebase already has useful installer building blocks in the older/stable project:

- Windows packaging scripts
- Linux `.run` builder flow
- Windows install bootstrap
- Linux install scripts

The recommended direction is not to invent a separate third packaging system. Instead:

- adapt the stable installer ideas
- point them at `Control Center Next`
- and make them platform-aware for the new product structure

## Expected Outcome

After this work, the project should be able to publish public GitHub releases where a user can pick one installer for:

- Windows
- Ubuntu x86_64
- Ubuntu arm64

and the installer will not stop at “UI copied”. It will attempt to deliver a machine that is actually ready to use.

That is the key difference between deployment convenience and a real product installer, and this design explicitly chooses the second.
