from __future__ import annotations

from backend.app.services.script_runner import run_launcher_by_platform


REPAIR_METADATA = {
    "install": {
        "title": "Popravka instalacije",
        "successSummary": "Popravka instalacije je zavrsena.",
        "failureSummary": "Popravka instalacije nije uspela.",
        "successMessage": "Zavrsili smo proveru i popravku osnovne instalacije aplikacije.",
        "failureMessage": "Nazalost, nismo uspeli da zavrsimo popravku instalacije iz prvog pokusaja.",
        "successNextStep": "Otvorite Home i proverite da li se Control Center sada normalno pokrece.",
        "failureNextStep": "Otvorite Detalji i posaljite nam poslednju poruku o gresci ako vam i dalje treba pomoc.",
    },
    "model": {
        "title": "Popravka modela",
        "successSummary": "Popravka modela je zavrsena.",
        "failureSummary": "Popravka modela nije uspela.",
        "successMessage": "Zavrsili smo proveru modela i pripremili ga za novo pokretanje.",
        "failureMessage": "Nazalost, nismo uspeli da popravimo model automatski iz ovog pokusaja.",
        "successNextStep": "Otvorite Models ili Home i proverite da li model sada izgleda spremno za rad.",
        "failureNextStep": "Otvorite Detalji i proverite sta je prijavljeno za model, pa nam posaljite tu poruku ako treba sledeci korak.",
    },
    "runtime": {
        "title": "Popravka runtime-a",
        "successSummary": "Popravka runtime-a je zavrsena.",
        "failureSummary": "Popravka runtime-a nije uspela.",
        "successMessage": "Zavrsili smo korake da ponovo pokrenemo runtime i vratimo server u zdravo stanje.",
        "failureMessage": "Nazalost, nismo uspeli da vratimo runtime u zdravo stanje iz ovog pokusaja.",
        "successNextStep": "Otvorite Home i proverite da li runtime sada ima zdrav status.",
        "failureNextStep": "Otvorite Detalji i pogledajte poslednju poruku o runtime gresci pre sledeceg pokusaja.",
    },
    "config": {
        "title": "Popravka podesavanja",
        "successSummary": "Popravka podesavanja je zavrsena.",
        "failureSummary": "Popravka podesavanja nije uspela.",
        "successMessage": "Vratili smo najvaznija podesavanja u stanje koje aplikacija moze bezbedno da koristi.",
        "failureMessage": "Nazalost, nismo uspeli da vratimo podesavanja u bezbedno stanje iz ovog pokusaja.",
        "successNextStep": "Otvorite Settings i proverite da li sada sve izgleda smisleno za nastavak rada.",
        "failureNextStep": "Otvorite Detalji i proverite poruku o gresci pre nego sto menjate dodatna podesavanja.",
    },
}


def _wrap_repair_result(repair_kind: str, payload: dict[str, object]) -> dict[str, object]:
    metadata = REPAIR_METADATA[repair_kind]
    is_success = payload.get("status") == "ok"

    summary = metadata["successSummary"] if is_success else metadata["failureSummary"]
    user_message = metadata["successMessage"] if is_success else metadata["failureMessage"]
    next_step = metadata["successNextStep"] if is_success else metadata["failureNextStep"]

    return {
        **payload,
        "repairKind": repair_kind,
        "title": metadata["title"],
        "summary": summary,
        "userMessage": user_message,
        "nextStep": next_step,
        "safeForNonTechnicalUsers": True,
    }


def run_repair_install() -> dict[str, object]:
    payload = run_launcher_by_platform("repair-install.sh", "repair-install.ps1")
    return _wrap_repair_result("install", payload)


def run_repair_model() -> dict[str, object]:
    payload = run_launcher_by_platform("repair-model.sh", "repair-model.ps1")
    return _wrap_repair_result("model", payload)


def run_repair_runtime() -> dict[str, object]:
    payload = run_launcher_by_platform("repair-runtime.sh", "repair-runtime.ps1")
    return _wrap_repair_result("runtime", payload)


def run_repair_config() -> dict[str, object]:
    payload = run_launcher_by_platform("repair-config.sh", "repair-config.ps1")
    return _wrap_repair_result("config", payload)
