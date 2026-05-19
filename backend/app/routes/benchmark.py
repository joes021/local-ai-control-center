from fastapi import APIRouter

from backend.app.services.benchmark_service import (
    clear_benchmark_history,
    list_batteries,
    load_battery_selection,
    load_benchmark_summary,
    restore_default_batteries,
    save_battery,
    start_battery_benchmark,
    start_selected_benchmark,
)


router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


@router.get("")
def benchmark_summary():
    return load_benchmark_summary()


@router.post("/run-selected")
def benchmark_run_selected(payload: dict[str, object]):
    return start_selected_benchmark(str(payload.get("scenarioId", "") or ""))


@router.post("/run-battery")
def benchmark_run_battery(payload: dict[str, object]):
    return start_battery_benchmark(str(payload.get("batteryId", "") or ""))


@router.get("/run-status")
def benchmark_run_status():
    return load_benchmark_summary().get("activeRun", {})


@router.get("/batteries")
def benchmark_batteries():
    return list_batteries()


@router.post("/batteries/save")
def benchmark_save_battery(payload: dict[str, object]):
    scenarios = payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else []
    return save_battery(str(payload.get("name", "") or ""), scenarios)


@router.post("/batteries/load")
def benchmark_load_battery(payload: dict[str, object]):
    return load_battery_selection(str(payload.get("batteryId", "") or ""))


@router.post("/batteries/restore-defaults")
def benchmark_restore_defaults():
    return restore_default_batteries()


@router.post("/clear-history")
def benchmark_clear_history_route():
    return clear_benchmark_history()


@router.get("/history")
def benchmark_history():
    return {"savedRuns": load_benchmark_summary().get("savedRuns", [])}
