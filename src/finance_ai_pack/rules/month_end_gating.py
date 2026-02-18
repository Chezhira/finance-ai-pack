from __future__ import annotations

import json
from pathlib import Path


RED = "RED"
AMBER = "AMBER"
GREEN = "GREEN"


def evaluate(unmatched_transactions: int, unexplained_amount: float) -> str:
    if unmatched_transactions >= 6 or unexplained_amount > 1000:
        return RED
    if unmatched_transactions > 0 or unexplained_amount > 0:
        return AMBER
    return GREEN


def can_proceed(status: str, overrides_file: Path) -> bool:
    if status != RED:
        return True
    overrides = json.loads(overrides_file.read_text())
    return bool(overrides)
