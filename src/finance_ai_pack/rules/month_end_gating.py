from __future__ import annotations

import json
from pathlib import Path


RED = "RED"
AMBER = "AMBER"
GREEN = "GREEN"

RULES_FILE = Path(__file__).resolve().parent / "gating_rules.yml"


def _load_thresholds() -> dict:
    thresholds = {
        "green": {"max_unmatched_transactions": 0, "max_unexplained_amount": 0.0, "max_vat_monthly_difference": 0.0},
        "amber": {"max_unmatched_transactions": 5, "max_unexplained_amount": 1000.0, "max_vat_monthly_difference": 250.0},
    }
    if not RULES_FILE.exists():
        return thresholds

    section = None
    level = None
    for raw in RULES_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "green:":
            section = "green"
            level = "thresholds"
            continue
        if line == "amber:":
            section = "amber"
            level = "thresholds"
            continue
        if line.endswith(":"):
            if line[:-1] not in {"green", "amber"}:
                level = line[:-1]
            continue
        if level == "thresholds" and section and ":" in line:
            key, value = [x.strip() for x in line.split(":", 1)]
            if key.startswith("max_"):
                thresholds[section][key] = float(value) if "." in value else int(value)
    return thresholds


def evaluate(unmatched_transactions: int, unexplained_amount: float, vat_monthly_differences: list[float] | None = None) -> str:
    thresholds = _load_thresholds()
    amber = thresholds.get("amber", {})
    green = thresholds.get("green", {})

    vat_monthly_differences = vat_monthly_differences or []
    max_vat_diff = max((abs(float(x)) for x in vat_monthly_differences), default=0.0)

    if (
        unmatched_transactions > int(amber.get("max_unmatched_transactions", 0))
        or unexplained_amount > float(amber.get("max_unexplained_amount", 0))
        or max_vat_diff > float(amber.get("max_vat_monthly_difference", 0))
    ):
        return RED

    if (
        unmatched_transactions > int(green.get("max_unmatched_transactions", 0))
        or unexplained_amount > float(green.get("max_unexplained_amount", 0))
        or max_vat_diff > float(green.get("max_vat_monthly_difference", 0))
    ):
        return AMBER

    return GREEN


def can_proceed(status: str, overrides_file: Path) -> bool:
    if status != RED:
        return True
    overrides = json.loads(overrides_file.read_text())
    return bool(overrides)
