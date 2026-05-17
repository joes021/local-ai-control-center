from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.local_qwen_state import load_local_qwen_summary
from backend.app.services.platform_config import get_target_platform
from backend.app.services.script_runner import run_linux_launcher, run_windows_launcher


_RUN_LOCK = threading.Lock()


DEFAULT_SCENARIOS = [
    {
        "id": "short",
        "name": "Short",
        "prompt": "Reply with exactly OK",
        "description": "Kratak smoke test za osnovni throughput signal.",
    },
    {
        "id": "medium",
        "name": "Medium",
        "prompt": "Summarize in 5 bullet points what local model serving means for a desktop workflow.",
        "description": "Srednji genericki scenario za kratak odgovor.",
    },
    {
        "id": "long",
        "name": "Long",
        "prompt": "Explain how KV cache compression changes memory usage, latency, and quality tradeoffs for local inference in a clear step-by-step format.",
        "description": "Duz i objasnjavajuci scenario za duzi odgovor.",
    },
    {
        "id": "code",
        "name": "Code",
        "prompt": "Write a short Python function that retries an HTTP request three times and explain it in one paragraph.",
        "description": "Kod scenario za code-like output.",
    },
]


def _state_dir() -> Path:
    path = detect_local_qwen_home() / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _history_path() -> Path:
    return _state_dir() / "token-metrics-history.json"


def _benchmark_batteries_path() -> Path:
    return _state_dir() / "benchmark-batteries.json"


def _benchmark_run_state_path() -> Path:
    return _state_dir() / "benchmark-run-state.json"


def _benchmark_history_runs_path() -> Path:
    return _state_dir() / "benchmark-history.json"


def _latest_log_path() -> Path | None:
    logs_dir = detect_local_qwen_home() / "logs"
    if not logs_dir.is_dir():
        return None
    candidates = sorted(logs_dir.glob("llama-*.err.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        candidates = sorted(logs_dir.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _read_json(path: Path, default):
    if not path.is_file():
        return deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return deepcopy(default)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _tail_lines(path: Path | None, limit: int = 30) -> list[str]:
    if path is None or not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    return lines[-limit:]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_battery_payload() -> dict[str, object]:
    return {
        "activeBatteryId": "default",
        "batteries": [
            {
                "id": "default",
                "name": "Default battery",
                "source": "default",
                "updatedAt": _now_iso(),
                "scenarios": deepcopy(DEFAULT_SCENARIOS),
            }
        ],
    }


def _idle_run_state() -> dict[str, object]:
    return {
        "runId": "",
        "status": "idle",
        "mode": "idle",
        "batteryId": "",
        "batteryName": "",
        "scenarioId": "",
        "scenarioName": "",
        "currentScenarioId": "",
        "currentScenarioName": "",
        "currentIndex": 0,
        "totalScenarios": 0,
        "percent": 0,
        "startedAt": "",
        "finishedAt": "",
        "message": "Benchmark nije pokrenut.",
        "scenarioStatuses": [],
    }


def _load_history() -> list[dict[str, object]]:
    payload = _read_json(_history_path(), [])
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _average(history: list[dict[str, object]], key: str) -> float:
    if not history:
        return 0.0
    values = [float(item.get(key, 0.0) or 0.0) for item in history]
    return round(sum(values) / len(values), 2)


def _trend(history: list[dict[str, object]], key: str, up_threshold: float, down_threshold: float) -> dict[str, str]:
    if len(history) < 2:
        return {
            "direction": "flat",
            "label": "stabilan",
            "signal": "=",
            "reason": "Jos nema dovoljno podataka za trend.",
        }
    first = float(history[0].get(key, 0.0) or 0.0)
    last = float(history[-1].get(key, 0.0) or 0.0)
    delta = last - first
    if delta >= up_threshold:
        return {
            "direction": "up",
            "label": "raste",
            "signal": "^",
            "reason": "Skorasnji signal deluje bolji nego ranije u uzorku.",
        }
    if delta <= down_threshold:
        return {
            "direction": "down",
            "label": "pada",
            "signal": "v",
            "reason": "Skorasnji signal deluje slabiji nego ranije u uzorku.",
        }
    return {
        "direction": "flat",
        "label": "stabilan",
        "signal": "=",
        "reason": "Signal nema veliku promenu kroz poslednje zahteve.",
    }


def _detect_source(label: str) -> str:
    normalized = str(label or "").lower()
    if "test" in normalized or "benchmark" in normalized:
        return "testPrompt"
    if "opencode" in normalized:
        return "opencode"
    return "other"


def _chart_label(measured_at: str) -> str:
    text = str(measured_at or "").strip()
    if not text:
        return "--:--:--"
    try:
        normalized = text.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).strftime("%H:%M:%S")
    except Exception:
        return text[-8:] if len(text) >= 8 else text


def _load_batteries() -> dict[str, object]:
    payload = _read_json(_benchmark_batteries_path(), _default_battery_payload())
    batteries = payload.get("batteries")
    if not isinstance(batteries, list) or not batteries:
        payload = _default_battery_payload()
    return payload


def _save_batteries(payload: dict[str, object]) -> None:
    _write_json(_benchmark_batteries_path(), payload)


def _load_run_state() -> dict[str, object]:
    payload = _read_json(_benchmark_run_state_path(), _idle_run_state())
    if not isinstance(payload, dict):
        return _idle_run_state()
    return {**_idle_run_state(), **payload}


def _save_run_state(payload: dict[str, object]) -> None:
    _write_json(_benchmark_run_state_path(), payload)


def _load_saved_runs() -> list[dict[str, object]]:
    payload = _read_json(_benchmark_history_runs_path(), [])
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _append_saved_run(payload: dict[str, object]) -> None:
    runs = _load_saved_runs()
    runs.insert(0, payload)
    _write_json(_benchmark_history_runs_path(), runs[:50])


def _selected_battery(payload: dict[str, object]) -> dict[str, object]:
    active_id = str(payload.get("activeBatteryId", "default") or "default")
    for battery in payload.get("batteries", []):
        if isinstance(battery, dict) and str(battery.get("id")) == active_id:
            return battery
    return payload["batteries"][0]


def _build_recent_activities(history: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, int]]:
    recent_activities = []
    source_counts = {"testPrompt": 0, "opencode": 0, "other": 0}
    for item in reversed(history[-10:]):
        source = _detect_source(str(item.get("label", "")))
        source_counts[source] += 1
        recent_activities.append(
            {
                "measuredAt": item.get("measuredAt"),
                "chartLabel": _chart_label(str(item.get("measuredAt", ""))),
                "label": item.get("label"),
                "source": source,
                "totalMs": round(float(item.get("totalMs", 0.0) or 0.0), 2),
                "totalTokensPerSecond": round(float(item.get("totalTokensPerSecond", 0.0) or 0.0), 2),
            }
        )
    return recent_activities, source_counts


def _load_profile() -> str:
    summary = load_local_qwen_summary()
    return str(summary.get("profile", "balanced") or "balanced")


def _run_scenario_prompt(prompt: str, *, label: str) -> dict[str, object]:
    profile = _load_profile()
    if get_target_platform() == "windows":
        return run_windows_launcher("test-prompt.ps1", "-Profile", profile, "-Prompt", prompt)
    return run_linux_launcher("test-prompt.sh", profile, prompt)


def _scenario_status_payload(scenarios: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "scenarioId": str(item.get("id", "")),
            "scenarioName": str(item.get("name", "")),
            "status": "queued",
            "summary": "Ceka pokretanje.",
        }
        for item in scenarios
    ]


def start_selected_benchmark(scenario_id: str) -> dict[str, object]:
    batteries_payload = _load_batteries()
    battery = _selected_battery(batteries_payload)
    scenarios = [item for item in battery.get("scenarios", []) if isinstance(item, dict)]
    selected = next((item for item in scenarios if str(item.get("id")) == scenario_id), None)
    if not selected:
        return {"status": "error", "summary": f"Scenario nije pronadjen: {scenario_id}"}

    with _RUN_LOCK:
        active = _load_run_state()
        if str(active.get("status")) in {"queued", "running"}:
            return {"status": "error", "summary": "Benchmark je vec pokrenut."}

        run_id = f"bench-{uuid4().hex[:10]}"
        run_state = {
            "runId": run_id,
            "status": "queued",
            "mode": "selected",
            "batteryId": str(battery.get("id", "")),
            "batteryName": str(battery.get("name", "")),
            "scenarioId": str(selected.get("id", "")),
            "scenarioName": str(selected.get("name", "")),
            "currentScenarioId": str(selected.get("id", "")),
            "currentScenarioName": str(selected.get("name", "")),
            "currentIndex": 1,
            "totalScenarios": 1,
            "percent": 0,
            "startedAt": _now_iso(),
            "finishedAt": "",
            "message": f"Pokrecem benchmark scenario: {selected.get('name')}",
            "scenarioStatuses": [
                {
                    "scenarioId": str(selected.get("id", "")),
                    "scenarioName": str(selected.get("name", "")),
                    "status": "queued",
                    "summary": "Ceka pokretanje.",
                }
            ],
        }
        _save_run_state(run_state)
        thread = threading.Thread(target=_run_selected_worker, args=(run_id, selected), daemon=True)
        thread.start()
    return {"status": "accepted", "summary": "Benchmark test je pokrenut.", "runId": run_id}


def _run_selected_worker(run_id: str, scenario: dict[str, object]) -> None:
    run_state = _load_run_state()
    if run_state.get("runId") != run_id:
        return
    run_state["status"] = "running"
    run_state["percent"] = 5
    run_state["scenarioStatuses"][0]["status"] = "running"
    run_state["scenarioStatuses"][0]["summary"] = "Scenario se izvrsava."
    _save_run_state(run_state)

    result = _run_scenario_prompt(str(scenario.get("prompt", "")), label=f"benchmark-{scenario.get('id')}")
    history = _load_history()
    latest_metric = history[-1] if history else {}
    final_status = "done" if result.get("status") == "ok" else "failed"

    run_state["status"] = final_status
    run_state["percent"] = 100
    run_state["finishedAt"] = _now_iso()
    run_state["message"] = str(result.get("summary", "Benchmark je zavrsen."))
    run_state["scenarioStatuses"][0]["status"] = final_status
    run_state["scenarioStatuses"][0]["summary"] = run_state["message"]
    _save_run_state(run_state)

    _append_saved_run(
        {
            "runId": run_id,
            "mode": "selected",
            "batteryName": run_state.get("batteryName", ""),
            "scenarioName": run_state.get("scenarioName", ""),
            "modelId": load_local_qwen_summary().get("activeModel", "unknown"),
            "runtime": load_local_qwen_summary().get("runtime", {}).get("active", "unknown"),
            "status": final_status,
            "startedAt": run_state.get("startedAt", ""),
            "finishedAt": run_state.get("finishedAt", ""),
            "currentMetric": latest_metric,
        }
    )


def start_battery_benchmark(battery_id: str) -> dict[str, object]:
    batteries_payload = _load_batteries()
    battery = next(
        (
            item
            for item in batteries_payload.get("batteries", [])
            if isinstance(item, dict) and str(item.get("id")) == battery_id
        ),
        None,
    )
    if not battery:
        return {"status": "error", "summary": f"Baterija nije pronadjena: {battery_id}"}
    scenarios = [item for item in battery.get("scenarios", []) if isinstance(item, dict)]
    if not scenarios:
        return {"status": "error", "summary": "Baterija nema nijedan scenario."}

    with _RUN_LOCK:
        active = _load_run_state()
        if str(active.get("status")) in {"queued", "running"}:
            return {"status": "error", "summary": "Benchmark je vec pokrenut."}

        run_id = f"bench-{uuid4().hex[:10]}"
        run_state = {
            "runId": run_id,
            "status": "queued",
            "mode": "battery",
            "batteryId": str(battery.get("id", "")),
            "batteryName": str(battery.get("name", "")),
            "scenarioId": "",
            "scenarioName": "",
            "currentScenarioId": "",
            "currentScenarioName": "",
            "currentIndex": 0,
            "totalScenarios": len(scenarios),
            "percent": 0,
            "startedAt": _now_iso(),
            "finishedAt": "",
            "message": f"Pokrecem full battery: {battery.get('name')}",
            "scenarioStatuses": _scenario_status_payload(scenarios),
        }
        _save_run_state(run_state)
        thread = threading.Thread(target=_run_battery_worker, args=(run_id, battery, scenarios), daemon=True)
        thread.start()
    return {"status": "accepted", "summary": "Full battery benchmark je pokrenut.", "runId": run_id}


def _run_battery_worker(run_id: str, battery: dict[str, object], scenarios: list[dict[str, object]]) -> None:
    run_state = _load_run_state()
    if run_state.get("runId") != run_id:
        return
    run_state["status"] = "running"
    _save_run_state(run_state)
    scenario_results: list[dict[str, object]] = []

    for index, scenario in enumerate(scenarios, start=1):
        run_state = _load_run_state()
        if run_state.get("runId") != run_id:
            return
        run_state["currentIndex"] = index
        run_state["currentScenarioId"] = str(scenario.get("id", ""))
        run_state["currentScenarioName"] = str(scenario.get("name", ""))
        run_state["percent"] = round(((index - 1) / len(scenarios)) * 100)
        run_state["message"] = f"Pokrecem scenario {index}/{len(scenarios)}: {scenario.get('name')}"
        run_state["scenarioStatuses"][index - 1]["status"] = "running"
        run_state["scenarioStatuses"][index - 1]["summary"] = "Scenario se izvrsava."
        _save_run_state(run_state)

        result = _run_scenario_prompt(str(scenario.get("prompt", "")), label=f"benchmark-{scenario.get('id')}")
        history = _load_history()
        latest_metric = history[-1] if history else {}
        status = "done" if result.get("status") == "ok" else "failed"
        scenario_results.append(
            {
                "scenarioId": str(scenario.get("id", "")),
                "scenarioName": str(scenario.get("name", "")),
                "status": status,
                "summary": str(result.get("summary", "")),
                "metric": latest_metric,
            }
        )
        run_state = _load_run_state()
        if run_state.get("runId") != run_id:
            return
        run_state["scenarioStatuses"][index - 1]["status"] = status
        run_state["scenarioStatuses"][index - 1]["summary"] = str(result.get("summary", ""))
        run_state["percent"] = round((index / len(scenarios)) * 100)
        _save_run_state(run_state)

    final_status = "done" if all(item["status"] == "done" for item in scenario_results) else "failed"
    run_state = _load_run_state()
    if run_state.get("runId") != run_id:
        return
    run_state["status"] = final_status
    run_state["finishedAt"] = _now_iso()
    run_state["message"] = "Benchmark battery je zavrsen." if final_status == "done" else "Benchmark battery je zavrsen sa greskama."
    _save_run_state(run_state)

    _append_saved_run(
        {
            "runId": run_id,
            "mode": "battery",
            "batteryName": str(battery.get("name", "")),
            "scenarioName": "",
            "modelId": load_local_qwen_summary().get("activeModel", "unknown"),
            "runtime": load_local_qwen_summary().get("runtime", {}).get("active", "unknown"),
            "status": final_status,
            "startedAt": run_state.get("startedAt", ""),
            "finishedAt": run_state.get("finishedAt", ""),
            "scenarioResults": scenario_results,
        }
    )


def save_battery(name: str, scenarios: list[dict[str, object]]) -> dict[str, object]:
    normalized_name = str(name or "").strip() or "Custom battery"
    normalized_scenarios = []
    for index, item in enumerate(scenarios, start=1):
        if not isinstance(item, dict):
            continue
        prompt = str(item.get("prompt", "") or "").strip()
        if not prompt:
            continue
        normalized_scenarios.append(
            {
                "id": str(item.get("id", f"custom-{index}") or f"custom-{index}"),
                "name": str(item.get("name", f"Custom {index}") or f"Custom {index}"),
                "prompt": prompt,
                "description": str(item.get("description", "") or "").strip(),
            }
        )
    if not normalized_scenarios:
        return {"status": "error", "summary": "Baterija mora imati bar jedan scenario."}

    payload = _load_batteries()
    battery_id = f"custom-{uuid4().hex[:8]}"
    battery = {
        "id": battery_id,
        "name": normalized_name,
        "source": "custom",
        "updatedAt": _now_iso(),
        "scenarios": normalized_scenarios,
    }
    payload["batteries"] = [
        item
        for item in payload.get("batteries", [])
        if not (isinstance(item, dict) and str(item.get("name")).lower() == normalized_name.lower())
    ]
    payload["batteries"].append(battery)
    payload["activeBatteryId"] = battery_id
    _save_batteries(payload)
    return {"status": "ok", "summary": f"Baterija sacuvana: {normalized_name}", "battery": battery}


def load_battery_selection(battery_id: str) -> dict[str, object]:
    payload = _load_batteries()
    match = next(
        (
            item
            for item in payload.get("batteries", [])
            if isinstance(item, dict) and str(item.get("id")) == battery_id
        ),
        None,
    )
    if not match:
        return {"status": "error", "summary": f"Baterija nije pronadjena: {battery_id}"}
    payload["activeBatteryId"] = battery_id
    _save_batteries(payload)
    return {"status": "ok", "summary": f"Ucitanа baterija: {match.get('name')}", "battery": match}


def restore_default_batteries() -> dict[str, object]:
    payload = _default_battery_payload()
    _save_batteries(payload)
    return {"status": "ok", "summary": "Podrazumevani benchmark testovi su vraceni.", "battery": payload["batteries"][0]}


def list_batteries() -> dict[str, object]:
    payload = _load_batteries()
    return {
        "batteries": payload.get("batteries", []),
        "selectedBattery": _selected_battery(payload),
    }


def load_benchmark_summary() -> dict[str, object]:
    history = _load_history()
    current = history[-1] if history else None
    recent_activities, source_counts = _build_recent_activities(history)
    batteries_payload = _load_batteries()
    selected_battery = _selected_battery(batteries_payload)
    active_run = _load_run_state()
    saved_runs = _load_saved_runs()

    chart_history = []
    for item in history[-20:]:
        copy_item = dict(item)
        copy_item["chartLabel"] = _chart_label(str(item.get("measuredAt", "")))
        chart_history.append(copy_item)

    return {
        "current": current,
        "history": chart_history,
        "historyCount": len(history),
        "requestCount": len(history),
        "lastMeasuredAt": current.get("measuredAt") if current else None,
        "lastLabel": current.get("label") if current else None,
        "activity": {
            "averageTotalMs": _average(history, "totalMs"),
            "sources": source_counts,
            "recentActivities": recent_activities,
            "stability": {
                "level": "warming" if len(history) < 3 else "stable",
                "label": "zagreva se" if len(history) < 3 else "stabilno",
                "score": 50 if len(history) < 3 else 85,
                "reason": "Treba jos nekoliko zahteva za pouzdaniji signal." if len(history) < 3 else "Skorasnji zahtevi deluju ujednaceno.",
            },
            "throughputTrend": _trend(history[-4:], "totalTokensPerSecond", 1.5, -1.5),
            "latencyTrend": _trend(history[-4:], "totalMs", 400.0, -400.0),
        },
        "averages": {
            "promptTokensPerSecond": _average(history, "promptTokensPerSecond"),
            "completionTokensPerSecond": _average(history, "completionTokensPerSecond"),
            "totalTokensPerSecond": _average(history, "totalTokensPerSecond"),
        },
        "liveLog": {
            "path": str(_latest_log_path()) if _latest_log_path() else "",
            "lines": _tail_lines(_latest_log_path(), 30),
        },
        "batteries": batteries_payload.get("batteries", []),
        "selectedBattery": selected_battery,
        "activeRun": active_run,
        "savedRuns": saved_runs[:20],
    }
