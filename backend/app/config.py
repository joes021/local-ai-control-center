from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class BackendConfig:
    host: str = "127.0.0.1"
    access_mode: str = "local-only"
    start_port: int = 3210
    end_port: int = 3299
    ui_port: int = 3210
    state_dir: Path = Path(__file__).resolve().parents[2] / "state"
    frontend_dist_dir: Path = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def get_config() -> BackendConfig:
    base = BackendConfig()
    ui_port = int(os.environ.get("CONTROL_CENTER_NEXT_UI_PORT", str(base.start_port)))
    frontend_dist = os.environ.get("CONTROL_CENTER_NEXT_FRONTEND_DIST", "").strip()
    host = os.environ.get("CONTROL_CENTER_NEXT_HOST", base.host).strip() or base.host
    access_mode = os.environ.get("CONTROL_CENTER_NEXT_ACCESS_MODE", base.access_mode).strip() or base.access_mode
    return BackendConfig(
        host=host,
        access_mode=access_mode,
        start_port=base.start_port,
        end_port=base.end_port,
        ui_port=ui_port,
        state_dir=base.state_dir,
        frontend_dist_dir=Path(frontend_dist) if frontend_dist else base.frontend_dist_dir,
    )
