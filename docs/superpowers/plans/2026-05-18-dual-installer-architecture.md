# Dual Installer Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two real installer lines, `Classic Full` and `Unified Full`, on top of one shared installer core so both deliver a complete local AI installation instead of only a partial UI payload.

**Architecture:** Extract a shared install/runtime core from the currently split legacy and next installer logic, then layer two SKU payloads over it. `Classic Full` remains the stable legacy experience, while `Unified Full` installs the same core plus the entire `Next` control-center shell over the same `LocalQwenHome`.

**Tech Stack:** PowerShell, Bash, Python, Inno Setup, self-extracting `.run` packaging, GitHub Releases, shared `LocalQwenHome` state, legacy launcher/runtime scripts, Next FastAPI/React payload.

---

## File Structure

### Existing files to reuse or adapt

- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\install\windows\install.ps1`
  - Current complete Windows legacy install flow with runtime/bootstrap logic.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\install\linux\install.sh`
  - Current complete Linux legacy install flow with source clone/model/runtime logic.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux\build-runtime.sh`
  - Existing Linux runtime/TurboQuant build flow.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\config\profiles\defaults.json`
  - Source of truth for legacy runtime defaults and TurboQuant source metadata.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\install.ps1`
  - Current Next hybrid Windows install flow.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\install.sh`
  - Current Next hybrid Linux install flow.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release-all.ps1`
  - Current three-artifact release automation.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\version.json`
  - Current Next release metadata.
- `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\version.json`
  - Current legacy release metadata.

### New files to create

- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\docs\superpowers\specs\2026-05-18-dual-installer-architecture-design.md`
  - The approved architecture spec.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release\classic-support-matrix.template.json`
  - Support matrix template for Classic Full SKU.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release\unified-support-matrix.template.json`
  - Support matrix template for Unified Full SKU.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\shared\install-core.py`
  - Shared platform-neutral installer orchestration core.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\shared\install-contract.py`
  - Shared readiness/report contract utilities.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\classic\build-release.ps1`
  - Classic SKU release entrypoint.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\unified\build-release.ps1`
  - Unified SKU release entrypoint.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\release-notes-classic.txt`
  - Classic SKU release notes.
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\release-notes-unified.txt`
  - Unified SKU release notes.

### Test files to create

- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_dual_installer_versions.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_shared_install_core_contract.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_classic_full_release_layout.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_unified_full_release_layout.py`
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_dual_release_metadata.py`

## Task 1: Lock Version Parity Across Next, Legacy, and Installed Homes

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\version.json`
- Modify: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\version.json`
- Modify: `C:\Users\AzdahaI9\LocalQwenHome\version.json`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_dual_installer_versions.py`

- [ ] **Step 1: Write the failing version parity test**

```python
from pathlib import Path
import json


def test_next_legacy_and_local_versions_match():
    paths = [
        Path(r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\version.json"),
        Path(r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\version.json"),
        Path(r"C:\Users\AzdahaI9\LocalQwenHome\version.json"),
    ]
    versions = [json.loads(path.read_text(encoding="utf-8"))["version"] for path in paths]
    assert versions[0] == versions[1] == versions[2]
```

- [ ] **Step 2: Run test to verify current state**

Run: `python -m unittest tests.packaging.test_dual_installer_versions -v`
Expected: PASS if already aligned, FAIL otherwise.

- [ ] **Step 3: Add a shared release version note**

Update both repo-level version files so the same release number is explicitly used for:

- `Classic Full`
- `Unified Full`

Keep naming distinct, but version identical.

- [ ] **Step 4: Re-run test**

Run: `python -m unittest tests.packaging.test_dual_installer_versions -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add version.json "C:/Users/AzdahaI9/Documents/Local Qwen 3.635Ba3B on home computer/version.json" C:/Users/AzdahaI9/LocalQwenHome/version.json tests/packaging/test_dual_installer_versions.py
git commit -m "chore: align release versions for classic and unified installers"
```

## Task 2: Introduce Shared Installer Core Contract

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\shared\install-core.py`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\shared\install-contract.py`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_shared_install_core_contract.py`

- [ ] **Step 1: Write the failing shared-core contract test**

```python
from pathlib import Path


def test_shared_install_core_declares_required_components():
    content = Path(
        r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\shared\install-core.py"
    ).read_text(encoding="utf-8")
    assert "controlCenter" in content
    assert "llamaCppRuntime" in content
    assert "openCode" in content
    assert "turboQuantRuntime" in content
    assert "modelBootstrap" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_shared_install_core_contract -v`
Expected: FAIL because shared core does not exist yet.

- [ ] **Step 3: Create the shared contract module**

Implement one shared structure for readiness reporting:

- `controlCenter`
- `llamaCppRuntime`
- `openCode`
- `turboQuantRuntime`
- `modelBootstrap`
- `installRoot`
- `launcherPaths`
- `localUrl`
- `tailscaleUrl`

- [ ] **Step 4: Create the shared orchestration core**

Add platform-neutral helpers for:

- dependency readiness checks
- runtime source clone checks
- OpenCode readiness
- model bootstrap readiness
- install report generation

This core should not contain UI-specific branching.

- [ ] **Step 5: Re-run test**

Run: `python -m unittest tests.packaging.test_shared_install_core_contract -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add install/shared tests/packaging/test_shared_install_core_contract.py
git commit -m "feat: add shared installer core contract"
```

## Task 3: Refactor Linux Install Flow To Use Shared Core

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\install.sh`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\installer-tui.sh`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\linux\installer-gui.sh`
- Reference: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\install\linux\install.sh`
- Reference: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux\build-runtime.sh`
- Test: extend `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_install_success_matrix.py`

- [ ] **Step 1: Write the failing Linux shared-core usage test**

Add assertions that Linux installer now routes through shared install core and reports:

- `modelBootstrap`
- `turboQuantRuntime`
- `openCode`
- `llamaCppRuntime`

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_install_success_matrix -v`
Expected: FAIL

- [ ] **Step 3: Port the missing legacy Linux behaviors**

Bring back the real Linux install capabilities from the stable project:

- clone upstream `llama.cpp`
- clone TurboQuant source repo/branch
- install or verify `OpenCode`
- model bootstrap flow
- final install report with explicit component states

- [ ] **Step 4: Remove false `unsupported` assumptions for arm64**

Change Linux install semantics so ARM64:

- attempts TurboQuant if toolchain is present
- reports `failed` if build fails
- reports `unsupported` only when there is a real architecture limitation, not a placeholder policy

- [ ] **Step 5: Re-run test**

Run: `python -m unittest tests.packaging.test_install_success_matrix -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add install/linux tests/packaging/test_install_success_matrix.py
git commit -m "feat: refactor linux installer onto shared core"
```

## Task 4: Refactor Windows Install Flow To Use Shared Core

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\install.ps1`
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\install\windows\setup-bootstrap.cmd`
- Reference: `C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\install\windows\install.ps1`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_windows_installer_builder.py`

- [ ] **Step 1: Write the failing Windows shared-core behavior test**

Add assertions that Windows install script clearly handles:

- `OpenCode`
- `llama.cpp`
- `TurboQuant`
- `model bootstrap`
- final readiness report

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_windows_installer_builder -v`
Expected: FAIL

- [ ] **Step 3: Port missing stable Windows install behaviors**

Bring back from stable installer flow:

- richer dependency checks
- fuller runtime/bootstrap semantics
- clearer TurboQuant build attempt/reporting
- model bootstrap readiness

- [ ] **Step 4: Keep Next-specific overlay support**

Do not regress `Next` payload support. The shared core must still let Windows install the `Next` web/backend layer for `Unified Full`.

- [ ] **Step 5: Re-run test**

Run: `python -m unittest tests.packaging.test_windows_installer_builder -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add install/windows tests/packaging/test_windows_installer_builder.py
git commit -m "feat: refactor windows installer onto shared core"
```

## Task 5: Add Classic Full SKU Release Layout

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\classic\build-release.ps1`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release\classic-support-matrix.template.json`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_classic_full_release_layout.py`

- [ ] **Step 1: Write the failing Classic release layout test**

```python
from pathlib import Path


def test_classic_release_builder_exists():
    root = Path(r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next")
    assert (root / "packaging" / "classic" / "build-release.ps1").exists()
    assert (root / "packaging" / "release" / "classic-support-matrix.template.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_classic_full_release_layout -v`
Expected: FAIL

- [ ] **Step 3: Create Classic SKU release builder**

This builder must generate:

- Windows Classic `.exe`
- Ubuntu x86_64 Classic `.run`
- Ubuntu arm64 Classic `.run`

And attach Classic-specific support matrix metadata.

- [ ] **Step 4: Re-run test**

Run: `python -m unittest tests.packaging.test_classic_full_release_layout -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packaging/classic packaging/release/classic-support-matrix.template.json tests/packaging/test_classic_full_release_layout.py
git commit -m "feat: add classic full release sku scaffolding"
```

## Task 6: Add Unified Full SKU Release Layout

**Files:**
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\unified\build-release.ps1`
- Create: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release\unified-support-matrix.template.json`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_unified_full_release_layout.py`

- [ ] **Step 1: Write the failing Unified release layout test**

```python
from pathlib import Path


def test_unified_release_builder_exists():
    root = Path(r"C:\Users\AzdahaI9\Documents\local-qwen-control-center-next")
    assert (root / "packaging" / "unified" / "build-release.ps1").exists()
    assert (root / "packaging" / "release" / "unified-support-matrix.template.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_unified_full_release_layout -v`
Expected: FAIL

- [ ] **Step 3: Create Unified SKU release builder**

This builder must generate:

- Windows Unified `.exe`
- Ubuntu x86_64 Unified `.run`
- Ubuntu arm64 Unified `.run`

And package:

- shared runtime core
- legacy complete install behavior
- Next payload overlay

- [ ] **Step 4: Re-run test**

Run: `python -m unittest tests.packaging.test_unified_full_release_layout -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packaging/unified packaging/release/unified-support-matrix.template.json tests/packaging/test_unified_full_release_layout.py
git commit -m "feat: add unified full release sku scaffolding"
```

## Task 7: Extend Release Automation For Two SKU Families

**Files:**
- Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\packaging\release-all.ps1`
- Create/Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\release-notes-classic.txt`
- Create/Modify: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\release-notes-unified.txt`
- Test: `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\tests\packaging\test_dual_release_metadata.py`

- [ ] **Step 1: Write the failing dual release metadata test**

Add assertions that release automation references:

- 3 Classic artifacts
- 3 Unified artifacts
- separate support matrices or explicit SKU metadata

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.packaging.test_dual_release_metadata -v`
Expected: FAIL

- [ ] **Step 3: Update release automation**

`release-all.ps1` must produce:

- six installer artifacts total
- `checksums.txt`
- Classic support matrix
- Unified support matrix
- release notes for both SKU lines

- [ ] **Step 4: Re-run test**

Run: `python -m unittest tests.packaging.test_dual_release_metadata -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packaging/release-all.ps1 release-notes-classic.txt release-notes-unified.txt tests/packaging/test_dual_release_metadata.py
git commit -m "feat: add dual-sku release automation"
```

## Task 8: Verify Real Installer Outputs Locally

**Files:**
- Modify as needed from previous tasks

- [ ] **Step 1: Run packaging tests**

Run:

```bash
python -m unittest tests.packaging.test_dual_installer_versions tests.packaging.test_shared_install_core_contract tests.packaging.test_classic_full_release_layout tests.packaging.test_unified_full_release_layout tests.packaging.test_dual_release_metadata tests.packaging.test_install_success_matrix tests.packaging.test_linux_installer_payload tests.packaging.test_windows_installer_builder -v
```

Expected: PASS

- [ ] **Step 2: Build Windows installers**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\classic\build-release.ps1
powershell -ExecutionPolicy Bypass -File packaging\unified\build-release.ps1
```

Expected: two Windows `.exe` artifacts

- [ ] **Step 3: Build Linux installers**

Run:

```bash
bash packaging/linux/build-run-installer.sh <version> x86_64
bash packaging/linux/build-run-installer.sh <version> arm64
```

and equivalent per-SKU wrappers if introduced.

Expected: Classic and Unified `.run` artifacts for both Linux architectures

- [ ] **Step 4: Run aggregate release automation**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\release-all.ps1 -SkipGitPush -SkipReleasePublish
```

Expected: all six artifacts plus metadata in `dist`

- [ ] **Step 5: Commit**

```bash
git add packaging install tests release-notes-classic.txt release-notes-unified.txt
git commit -m "test: verify dual installer artifact generation"
```

## Task 9: Publish Spec + Plan + Dual Installer Work To Public GitHub

**Files:**
- Modify: whichever files changed during Tasks 1-8

- [ ] **Step 1: Push working branch**

Run:

```bash
git push origin codex/windows-control-center-next-adapter
```

Expected: branch updated

- [ ] **Step 2: Publish public release artifacts**

Run:

```bash
gh release create v<version> ...
```

Expected: GitHub release contains:

- 3 Classic artifacts
- 3 Unified artifacts
- checksums
- support matrices

- [ ] **Step 3: Verify release**

Run:

```bash
gh release view v<version>
```

Expected: release exists and asset list is complete

- [ ] **Step 4: Final commit if needed**

If release notes or metadata changed after publish:

```bash
git add ...
git commit -m "docs: finalize dual installer release metadata"
git push origin codex/windows-control-center-next-adapter
```

## Task 10: Real Platform Validation

**Files:**
- No required source changes unless platform fixes are found

- [ ] **Step 1: Validate Windows full install**

Check:

- `Classic Full` works
- `Unified Full` works
- both use the same `LocalQwenHome`

- [ ] **Step 2: Validate Ubuntu x86_64 full install**

Check:

- `Classic Full` works
- `Unified Full` works
- `llama.cpp`
- `OpenCode`
- `TurboQuant`
- model bootstrap

- [ ] **Step 3: Validate Ubuntu arm64 full install**

Check:

- `Classic Full` works
- `Unified Full` works
- `llama.cpp`
- `OpenCode`
- model bootstrap
- `TurboQuant` is either working or clearly reported as failed/unsupported

- [ ] **Step 4: Patch and re-verify if any platform breaks**

Run only the smallest failing platform-specific verification after each fix.

- [ ] **Step 5: Commit**

```bash
git add ...
git commit -m "fix: close platform-specific gaps in dual installers"
```
