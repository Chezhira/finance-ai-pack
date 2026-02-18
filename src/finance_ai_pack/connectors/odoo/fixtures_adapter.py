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

    def get_vat_tax_lines(self, period: str, vat_type: str) -> list[dict]:
        fixture_file = self.fixtures_dir / "vat" / f"odoo_vat_lines_{period}.json"
        if not fixture_file.exists():
            return []
        rows = json.loads(fixture_file.read_text())
        return [
            {
                "period": period,
                "tax_type": row.get("tax_type", ""),
                "vat_amount": float(row.get("vat_amount", 0.0)),
                "document_ref": row.get("document_ref", ""),
                "move_type": row.get("move_type", ""),
                "source_period": row.get("source_period", period),
                "exception_hint": row.get("exception_hint", ""),
                "notes": row.get("notes", ""),
            }
            for row in rows
            if row.get("tax_type") == vat_type
        ]

    def get_vat_control_balance(self, period: str) -> dict:
        lines = [
            *self.get_vat_tax_lines(period=period, vat_type="input"),
            *self.get_vat_tax_lines(period=period, vat_type="output"),
        ]
        closing_balance = sum(float(row.get("vat_amount", 0.0)) for row in lines)
        return {
            "opening_balance": 0.0,
            "debits": round(sum(float(r.get("vat_amount", 0.0)) for r in lines if float(r.get("vat_amount", 0.0)) < 0), 2),
            "credits": round(sum(float(r.get("vat_amount", 0.0)) for r in lines if float(r.get("vat_amount", 0.0)) >= 0), 2),
            "closing_balance": round(closing_balance, 2),
            "assumption": "Fixture tie-out approximates VAT control using summed VAT tax lines only.",
        }
