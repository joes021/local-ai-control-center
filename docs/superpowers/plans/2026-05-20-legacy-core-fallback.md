# Legacy Core Fallback Execution Plan

Date: 2026-05-20

## Goal

Prebaciti `Unified` installer na stabilan fallback model:

- **legacy installer/runtime core** postaje izvor istine
- **Next** ostaje samo overlay sloj preko vec uspesne legacy instalacije

To znaci da novi installer vise ne sme da "proceni" da je model ili TurboQuant spreman. Mora da se osloni na stari dokazani tok za:

- dependency bootstrap
- repo/runtime bootstrap
- model download
- OpenCode wiring
- TurboQuant build

Tek kada je to zavrseno, `Next` payload i backend/frontend overlay smeju da se naslone preko istog install root-a.

## Hard Rules

1. Ako je izabran model, installer mora ili stvarno da ga preuzme ili da padne.
2. Ako je `Install TurboQuant` cekiran, installer mora ili stvarno da ga build-uje ili da padne.
3. `Next` installer ne sme vise da glumi sopstveni install core kada stable legacy core vec postoji.
4. `Next` overlay ne sme da degradira rad starog sistema.

## Execution Steps

### Step 1: Package legacy core into the new setup

- prosiriti Windows staging payload da nosi i:
  - `support/install/windows`
  - sve sto legacy install skripta ocekuje kao repo-root support
- patch-ovati staged legacy fajlove na novo brendiranje gde je bezbedno:
  - `LocalAIControlCenter`
  - `Local AI Control Center`

### Step 2: Introduce a delegated install path in the new Windows installer

- novi `install/windows/install.ps1` prvo razresava selected model i installer izbor
- ako je model custom/Unsloth/HF entry, registruje ga u legacy katalog pre delegacije
- zatim poziva staged legacy `support/install/windows/install.ps1`
- prosledjuje mu:
  - `InstallRoot`
  - `Profile`
  - `ModelId`
  - `SkipOpenCodeInstall`
  - `SkipModelDownload`
  - `SkipTurboQuantBuild`
  - `SkipDependencies`

### Step 3: Enforce post-legacy verification before Next overlay

- posle legacy core toka proveriti:
  - `install-state.json`
  - `modelFile`
  - `llama-server.exe`
  - `OpenCode`
  - `TurboQuant` kada je cekiran
- ako bilo sta obavezno fali, prekinuti instalaciju pre Next overlay-a

### Step 4: Apply Next overlay only after legacy success

- tek tada kopirati/pregaziti:
  - `backend`
  - `frontend/dist`
  - `launchers/windows`
  - `run_control_center_next.py`
- zatim poravnati:
  - `install-state.json`
  - `settings.json`
  - `runtime-config.json`
  - desktop shortcut-e

### Step 5: Add regression tests for fallback contract

- test da staging payload nosi `support/install/windows/install.ps1`
- test da novi installer delegira legacy core skripti
- test da `TurboQuant` checked => failure if missing
- test da selected model mismatch vise ne prolazi kao ready

### Step 6: Rebuild and publish a Windows hotfix

- build setup
- run packaging tests
- publish novi Windows release
- Linux ostaje nepromenjen dok se fallback model ne potvrdi i tamo

## Success Criteria

Installer je uspesan samo ako:

- selected model zaista postoji na disku
- `llama.cpp` binar postoji
- `OpenCode` postoji
- `TurboQuant` postoji kada je cekiran
- `Next` portal se dize preko istog install root-a

## Out of Scope

- novi Linux fallback cutover
- dodatni UI polish
- nove feature dorade u Browser/Benchmark/Updates

Prvo stabilizacija install core-a, pa tek onda sve ostalo.
