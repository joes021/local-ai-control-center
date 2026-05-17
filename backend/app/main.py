from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_config
from backend.app.routes.health import router as health_router
from backend.app.routes.logs import router as logs_router
from backend.app.routes.models import router as models_router
from backend.app.routes.repair import router as repair_router
from backend.app.routes.runtime import router as runtime_router
from backend.app.routes.settings import router as settings_router
from backend.app.routes.status import router as status_router
from backend.app.routes.system import router as system_router
from backend.app.routes.updates import router as updates_router


app = FastAPI(title="Local Qwen Control Center Next Backend")
app.include_router(health_router)
app.include_router(logs_router)
app.include_router(models_router)
app.include_router(repair_router)
app.include_router(runtime_router)
app.include_router(settings_router)
app.include_router(status_router)
app.include_router(system_router)
app.include_router(updates_router)

config = get_config()
if config.frontend_dist_dir.is_dir():
    assets_dir = config.frontend_dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/")
def frontend_index():
    index_path = get_config().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        return {
            "status": "error",
            "summary": "Frontend build nije pronadjen. Pokreni npm install i npm run build u frontend folderu.",
            "path": str(index_path),
        }
    return FileResponse(index_path)
