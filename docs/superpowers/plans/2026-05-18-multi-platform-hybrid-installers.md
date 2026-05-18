# Multi-Platform Hybrid Installers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish three real hybrid installers for `Local AI Control Center` that produce a usable system on Windows, Ubuntu x86_64, and Ubuntu arm64 instead of only copying the UI payload.

**Architecture:** Reuse the stable repo packaging approach for Windows `.exe` and Linux `.run` installers, but point the payload and runtime wiring at `local-qwen-control-center-next`. Introduce a shared installer payload layout for `Next`, then adapt platform installers to verify/install dependencies, `OpenCode`, `llama.cpp`, optional `TurboQuant`, and final subsystem readiness.

**Tech Stack:** PowerShell, Bash, Python, Inno Setup, self-extracting `.run` packaging, GitHub release automation, FastAPI/React payload assets.

---

## File Structure

### Existing files to reuse or adapt

- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\packaging\windows\build-setup.ps1`
  - Current Windows setup builder in the stable project.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\packaging\windows\LocalQwenSetup.iss`
  - Existing Inno Setup script.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\packaging\linux\build-run-installer.sh`
  - Existing Linux self-extracting `.run` builder.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\install\windows\install.ps1`
  - Existing Windows install/bootstrap flow with staged status reporting.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\install\linux\install.sh`
  - Existing Linux install/bootstrap flow with dependency checks and runtime install logic.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\launchers\windows\start-control-center-next.ps1`
  - Current Windows launcher for the Next app.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\launchers\linux\start-control-center-next.sh`
  - Current Linux launcher for the Next app.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\backend\app\services\local_qwen_state.py`
  - Builds status payload and version/runtime summary.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\package.json`
  - Versioned frontend package metadata.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\version.json`
  - Stable version file used by packaging scripts today.

### New files to create in `local-qwen-control-center-next`

- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\build-setup.ps1`
  - Next-specific Windows builder.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\LocalAIControlCenterSetup.iss`
  - Next-specific Inno Setup script.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\linux\build-run-installer.sh`
  - Next-specific Linux `.run` builder.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release-all.ps1`
  - Build/release automation for all three installer artifacts.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\install.ps1`
  - Next-specific Windows install/bootstrap flow.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\setup-bootstrap.cmd`
  - Windows bootstrap entrypoint if needed by Inno Setup.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\install.sh`
  - Next-specific Linux install/bootstrap flow.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\installer-tui.sh`
  - Linux TUI installer entrypoint.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\installer-gui.sh`
  - Linux GUI installer entrypoint if already viable.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release\support-matrix.template.json`
  - Template for generated support matrix metadata.

### Test files to create

- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_release_layout.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_linux_installer_payload.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_windows_installer_builder.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_install_success_matrix.py`

## Task 1: Scaffold Packaging Layout In The Next Repo

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\build-setup.ps1`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\LocalAIControlCenterSetup.iss`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\linux\build-run-installer.sh`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release-all.ps1`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_release_layout.py`

- [ ] **Step 1: Write the failing packaging layout test**

```python
from pathlib import Path


def test_packaging_layout_exists():
    root = Path(r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next")
    assert (root / "packaging" / "windows" / "build-setup.ps1").exists()
    assert (root / "packaging" / "windows" / "LocalAIControlCenterSetup.iss").exists()
    assert (root / "packaging" / "linux" / "build-run-installer.sh").exists()
    assert (root / "packaging" / "release-all.ps1").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_release_layout -v`
Expected: FAIL because the packaging files do not exist yet.

- [ ] **Step 3: Create the initial packaging directory and stub files**

Create minimal, non-empty script files that clearly state:

- Windows builder targets `local-qwen-control-center-next`
- Linux builder targets `local-qwen-control-center-next`
- release automation will emit:
  - Windows `.exe`
  - Linux x86_64 `.run`
  - Linux arm64 `.run`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.packaging.test_release_layout -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packaging tests/packaging
git commit -m "feat: scaffold multi-platform installer packaging layout"
```

## Task 2: Port Stable Windows Builder To Next

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\build-setup.ps1`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\LocalAIControlCenterSetup.iss`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_windows_installer_builder.py`

- [ ] **Step 1: Write the failing Windows builder test**

```python
from pathlib import Path


def test_windows_builder_targets_next_repo_assets():
    content = Path(
        r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\windows\build-setup.ps1"
    ).read_text(encoding="utf-8")
    assert "local-qwen-control-center-next" in content
    assert "Local AI Control Center" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_windows_installer_builder -v`
Expected: FAIL because the scaffolded builder is still a stub.

- [ ] **Step 3: Port the stable Windows builder**

Adapt these behaviors from the stable project:

- version loading from `version.json`
- Inno Setup resolution
- output artifact naming
- `a.b.c` version validation

But point it at the Next repo and Next installer files:

- app name = `Local AI Control Center`
- artifact name = `Local-AI-Control-Center-Setup-<ver>.exe`
- include Next payload folders:
  - `backend`
  - `frontend/dist`
  - `launchers`
  - `install`
  - `state` defaults if needed

- [ ] **Step 4: Update the Inno Setup script**

Ensure the installer:

- installs the Next payload
- launches Next bootstrap/install logic
- writes desktop entry/shortcut names using `Local AI Control Center`

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m unittest tests.packaging.test_windows_installer_builder -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packaging/windows tests/packaging/test_windows_installer_builder.py
git commit -m "feat: port windows hybrid installer to control center next"
```

## Task 3: Port Stable Linux Builder To Next With Dual-Arch Output

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\linux\build-run-installer.sh`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_linux_installer_payload.py`

- [ ] **Step 1: Write the failing Linux payload test**

```python
from pathlib import Path


def test_linux_builder_mentions_both_architectures():
    content = Path(
        r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\linux\build-run-installer.sh"
    ).read_text(encoding="utf-8")
    assert "x86_64" in content
    assert "arm64" in content
    assert "Local-AI-Control-Center-Setup-linux-" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_linux_installer_payload -v`
Expected: FAIL because the stub builder does not yet produce arch-specific artifacts.

- [ ] **Step 3: Port the stable Linux `.run` builder**

Adapt the stable builder to:

- package Next payload instead of stable payload
- include:
  - `backend`
  - `frontend/dist`
  - `launchers/linux`
  - `install/linux`
  - defaults/config assets
- emit two artifact names:
  - `Local-AI-Control-Center-Setup-linux-x86_64-<ver>.run`
  - `Local-AI-Control-Center-Setup-linux-arm64-<ver>.run`

- [ ] **Step 4: Make the Linux builder architecture-aware**

The payload may remain mostly shared, but the artifact metadata and install flow must clearly know:

- target architecture
- expected dependency/install path
- `TurboQuant` optional behavior for arm64

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m unittest tests.packaging.test_linux_installer_payload -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packaging/linux tests/packaging/test_linux_installer_payload.py
git commit -m "feat: add dual-arch linux run installer builder"
```

## Task 4: Create Next-Specific Windows Install Flow

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\install.ps1`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\setup-bootstrap.cmd`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\launchers\windows\start-control-center-next.ps1`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_install_success_matrix.py`

- [ ] **Step 1: Write the failing success-matrix test for Windows**

```python
from pathlib import Path


def test_windows_installer_declares_required_components():
    content = Path(
        r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\install.ps1"
    ).read_text(encoding="utf-8")
    assert "Control Center" in content
    assert "llama.cpp" in content
    assert "OpenCode" in content
    assert "TurboQuant" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_install_success_matrix -v`
Expected: FAIL because the Next Windows installer flow does not exist yet.

- [ ] **Step 3: Port the stable Windows install script**

Reuse the staged install model from the stable repo, but rewrite the payload assumptions for Next:

- Next repo layout
- Next launcher names
- Next frontend build path
- Next runtime state files

- [ ] **Step 4: Keep hard success conditions explicit**

Installer logic must fail if any of these remain missing:

- `Control Center`
- `llama.cpp`
- `OpenCode`

It may warn rather than fail for:

- `TurboQuant`

- [ ] **Step 5: Write the final readiness report**

Ensure Windows install writes a subsystem summary with:

- `Control Center`
- `llama.cpp`
- `OpenCode`
- `TurboQuant`
- install path
- local URL
- log path

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m unittest tests.packaging.test_install_success_matrix -v`
Expected: PASS for the Windows portion.

- [ ] **Step 7: Commit**

```bash
git add install/windows launchers/windows tests/packaging/test_install_success_matrix.py
git commit -m "feat: add windows hybrid installer flow for next"
```

## Task 5: Create Next-Specific Linux Install Flow

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\install.sh`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\installer-tui.sh`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\installer-gui.sh`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\launchers\linux\start-control-center-next.sh`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_install_success_matrix.py`

- [ ] **Step 1: Write the failing Linux installer test**

```python
from pathlib import Path


def test_linux_installer_declares_arm64_optional_turboquant():
    content = Path(
        r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\install.sh"
    ).read_text(encoding="utf-8")
    assert "python3" in content
    assert "node" in content
    assert "OpenCode" in content
    assert "llama.cpp" in content
    assert "TurboQuant" in content
    assert "arm64" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_install_success_matrix -v`
Expected: FAIL because the Next Linux installer flow does not yet exist.

- [ ] **Step 3: Port the stable Linux install script**

Adapt these responsibilities:

- package install checks
- `python3`, `venv`, `node`, `npm`
- `OpenCode`
- `llama.cpp`
- model handling
- desktop entry
- final summary

But point them at the Next repo structure and launchers.

- [ ] **Step 4: Add explicit architecture-aware branching**

Installer logic must distinguish:

- `x86_64`
- `arm64`

And must treat `TurboQuant` on arm64 as:

- optional
- status-reported
- never silently ignored

- [ ] **Step 5: Require success for the core trio**

Linux installer must fail if these are not ready:

- `Control Center`
- `llama.cpp`
- `OpenCode`

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m unittest tests.packaging.test_install_success_matrix -v`
Expected: PASS for the Linux portion.

- [ ] **Step 7: Commit**

```bash
git add install/linux launchers/linux tests/packaging/test_install_success_matrix.py
git commit -m "feat: add linux hybrid installer flow for next"
```

## Task 6: Wire Versioning, Artifact Naming, And Support Matrix

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release-all.ps1`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release\support-matrix.template.json`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\package.json`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\frontend\package-lock.json`
- Modify: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\version.json`
- Modify: `C:\Users\AzdahaI9\LocalQwenHome\version.json`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_release_layout.py`

- [ ] **Step 1: Write the failing release automation assertions**

```python
from pathlib import Path


def test_release_automation_mentions_three_primary_artifacts():
    content = Path(
        r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release-all.ps1"
    ).read_text(encoding="utf-8")
    assert "Local-AI-Control-Center-Setup-" in content
    assert "linux-x86_64" in content
    assert "linux-arm64" in content
    assert "checksums.txt" in content
    assert "support-matrix.json" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_release_layout -v`
Expected: FAIL because release automation is still incomplete.

- [ ] **Step 3: Implement release automation**

Release automation must:

- build Windows installer
- build Linux x86_64 installer
- build Linux arm64 installer
- generate:
  - `checksums.txt`
  - `release-notes.txt`
  - `support-matrix.json`

- [ ] **Step 4: Ensure public artifact names match the spec**

Required artifact names:

- `Local-AI-Control-Center-Setup-<version>.exe`
- `Local-AI-Control-Center-Setup-linux-x86_64-<version>.run`
- `Local-AI-Control-Center-Setup-linux-arm64-<version>.run`

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m unittest tests.packaging.test_release_layout -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packaging frontend/package.json frontend/package-lock.json "..\\Local Qwen 3.635Ba3B on home computer\\version.json" "C:\\Users\\AzdahaI9\\LocalQwenHome\\version.json"
git commit -m "feat: add multi-platform release automation and metadata"
```

## Task 7: Verify End-To-End Local Packaging

**Files:**
- Modify if needed: packaging and install scripts touched above
- Test: all packaging tests and targeted live build commands

- [ ] **Step 1: Run packaging test suite**

Run:

```bash
python -m unittest ^
  tests.packaging.test_release_layout ^
  tests.packaging.test_linux_installer_payload ^
  tests.packaging.test_windows_installer_builder ^
  tests.packaging.test_install_success_matrix -v
```

Expected: PASS

- [ ] **Step 2: Run frontend smoke tests that should still pass**

Run:

```bash
python -m unittest tests.frontend.test_ui_source_smoke -v
```

Expected: PASS

- [ ] **Step 3: Build Windows installer artifact locally**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build-setup.ps1 -Version 2.x.y
```

Expected: `.exe` artifact created in `dist\windows`

- [ ] **Step 4: Build Linux installer artifacts locally**

Run:

```bash
bash ./packaging/linux/build-run-installer.sh 2.x.y
```

Expected:

- `Local-AI-Control-Center-Setup-linux-x86_64-2.x.y.run`
- `Local-AI-Control-Center-Setup-linux-arm64-2.x.y.run`

- [ ] **Step 5: Run release automation dry run**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\release-all.ps1 -Version 2.x.y -SkipGitPush -SkipReleasePublish
```

Expected:

- all three primary artifacts
- `checksums.txt`
- `support-matrix.json`

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "test: verify multi-platform hybrid installer pipeline"
```

## Task 8: Validate Real Install Outcome On Target Machines

**Files:**
- No new code required unless fixes are discovered
- Validate with:
  - local Windows machine
  - Ubuntu x86_64 machine
  - Ubuntu arm64 machine

- [ ] **Step 1: Test Windows installer on a real machine**

Validate:

- `Control Center: OK`
- `llama.cpp: OK`
- `OpenCode: OK`
- `TurboQuant: OK/unavailable with explanation`

- [ ] **Step 2: Test Ubuntu x86_64 installer on a real machine**

Validate:

- `Control Center: OK`
- `llama.cpp: OK`
- `OpenCode: OK`
- `Run llama.cpp web` works

- [ ] **Step 3: Test Ubuntu arm64 installer on a real machine**

Validate:

- `Control Center: OK`
- `llama.cpp: OK`
- `OpenCode: OK`
- `TurboQuant` clearly reported as `OK`, `nije prisutan`, or `nije podržan`

- [ ] **Step 4: Fix any platform-specific failures**

Use small targeted commits rather than one large cleanup commit.

- [ ] **Step 5: Final verification**

Re-run:

```bash
python -m unittest tests.packaging.test_release_layout tests.packaging.test_linux_installer_payload tests.packaging.test_windows_installer_builder tests.packaging.test_install_success_matrix -v
python -m unittest tests.frontend.test_ui_source_smoke -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "fix: finalize multi-platform installer validation"
```
