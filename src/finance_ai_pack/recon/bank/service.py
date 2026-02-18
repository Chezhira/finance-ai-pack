from __future__ import annotations

from pathlib import Path
from finance_ai_pack.connectors.odoo.fixtures_adapter import load_statement_banks


def reconcile(period: str, fixtures_dir: Path) -> dict:
    return {
        "period": period,
        "banks": load_statement_banks(fixtures_dir),
        "proposed_journals": [],
        "exceptions": [],
    }
