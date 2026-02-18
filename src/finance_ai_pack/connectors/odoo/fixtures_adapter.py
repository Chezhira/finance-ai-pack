from __future__ import annotations

import json
from pathlib import Path


class FixturesAdapter:
    def __init__(self, fixtures_dir: Path) -> None:
        self.fixtures_dir = fixtures_dir

    def discover_bank_journals(self) -> list[dict]:
        payload = json.loads((self.fixtures_dir / "odoo_statement_lines" / "banks.json").read_text())
        journals: list[dict] = []
        for idx, bank in enumerate(payload, start=1):
            journals.append(
                {
                    "id": idx,
                    "name": bank.get("journal", bank["code"]),
                    "type": "bank",
                    "currency": bank.get("currency", ""),
                    "code": bank["code"],
                    "active": True,
                }
            )
        return journals

    def get_statement_lines(self, journal: dict, period: str) -> list[dict]:
        code = journal["code"]
        fixture_file = self.fixtures_dir / "odoo_statement_lines" / f"{code}_{period}.json"
        if not fixture_file.exists():
            return []
        lines = json.loads(fixture_file.read_text())
        enriched = []
        for row in lines:
            amount = float(row.get("amount", 0))
            enriched.append(
                {
                    "id": f"{code}:{row.get('reference', 'line')}:{row.get('date', '')}",
                    "date": row.get("date"),
                    "amount": amount,
                    "reference": row.get("reference", ""),
                    "payment_ref": row.get("reference", ""),
                    "is_reconciled": bool(row.get("is_reconciled", False)),
                    "move_line_count": int(row.get("move_line_count", 0)),
                }
            )
        return enriched

    def get_journal_balance(self, journal: dict, period: str) -> float:
        _ = period
        _ = journal
        return 0.0
