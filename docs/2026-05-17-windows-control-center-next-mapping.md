# Windows Control Center Next Mapping

## Cilj

Isti `Control Center Next` Web UI treba da radi i za Linux i za Windows, uz isti API contract i isti frontend.

## Shared ekran / route sloj

- `GET /api/status`
- `GET /api/models`
- `POST /api/models/activate`
- `POST /api/models/download`
- `POST /api/models/add-local`
- `POST /api/models/add-hf`
- `POST /api/models/add-unsloth`
- `POST /api/models/delete`
- `GET /api/settings`
- `POST /api/settings/apply`
- `GET /api/settings/turboquant`
- `POST /api/settings/turboquant-config`
- `POST /api/settings/turboquant-presets/save`
- `POST /api/settings/turboquant-presets/delete`
- `GET /api/logs`
- `POST /api/repair/install`
- `POST /api/repair/model`
- `POST /api/repair/runtime`
- `POST /api/repair/config`
- `GET /api/updates/check`
- `POST /api/updates/install`

## Linux -> Windows skripta mapa

| Shared action | Linux launcher | Windows launcher / helper |
| --- | --- | --- |
| settings apply | `configure-settings.sh` | `configure-settings.ps1` |
| start server | `start-server.sh` | `start-server.ps1` |
| stop server | `stop-server.sh` | `stop-server.ps1` |
| logs | `show-logs.sh` | `show-logs.ps1` |
| repair install | `repair-install.sh` | `repair-install.ps1` |
| repair model | `repair-model.sh` | `repair-model.ps1` |
| repair runtime | `repair-runtime.sh` | `repair-runtime.ps1` |
| repair config | `repair-config.sh` | `repair-config.ps1` |
| check updates | `check-updates.sh` | `check-updates.ps1` |
| install update | `install-update.sh` | `install-update.ps1` |
| model activate | `manage-models.sh use <id>` | `manage-models.ps1 -ModelId <id>` |
| model download | `manage-models.sh download <id>` | `manage-models.ps1 -ModelId <id> -Download` |
| add local model | `manage-models.sh add-local ...` | `Import-LocalGgufModel` helper |
| add HF model | `manage-models.sh add-hf ...` | `Add-HuggingFaceCustomModel` helper |
| add Unsloth model | `manage-models.sh add-unsloth ...` | `Add-UnslothCustomModel` helper |

## Prvi Windows parity milestone

1. Backend runner bira ciljnu platformu kroz env/config.
2. `status`, `settings`, `models` read tokovi ostaju shared.
3. `add-local`, `add-hf`, `add-unsloth`, `activate`, `download` dobijaju Windows adapter pozive.
4. Windows `start-server.ps1` poštuje isti `TurboQuant` config fajl kao Linux.
5. Stari Windows Control Center ostaje fallback dok novi Web UI ne prođe parity smoke.
