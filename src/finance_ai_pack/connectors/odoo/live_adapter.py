from __future__ import annotations

from datetime import datetime

from finance_ai_pack.connectors.odoo.client import OdooClient


class LiveOdooAdapter:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def discover_bank_journals(self) -> list[dict]:
        journals = self.client.search_read(
            "account.journal",
            [["active", "=", True], ["type", "in", ["bank", "cash"]]],
            fields=["id", "name", "type", "currency_id"],
            order="name asc",
        )
        normalized = []
        for row in journals:
            currency = ""
            if isinstance(row.get("currency_id"), list) and row["currency_id"]:
                currency = row["currency_id"][1]
            normalized.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row.get("type", "bank"),
                    "currency": currency,
                    "active": True,
                    "code": str(row["id"]),
                }
            )
        return normalized

    def get_statement_lines(self, journal: dict, period: str) -> list[dict]:
        start = f"{period}-01"
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        if start_dt.month == 12:
            end = f"{start_dt.year + 1}-01-01"
        else:
            end = f"{start_dt.year}-{start_dt.month + 1:02d}-01"

        lines = self.client.search_read(
            "account.bank.statement.line",
            [
                ["journal_id", "=", journal["id"]],
                ["date", ">=", start],
                ["date", "<", end],
            ],
            fields=[
                "id",
                "date",
                "amount",
                "payment_ref",
                "ref",
                "is_reconciled",
                "move_id",
                "move_name",
            ],
            order="date asc,id asc",
        )

        for row in lines:
            move_linked = 0
            move_id = row.get("move_id")
            if isinstance(move_id, list) and move_id:
                move_lines = self.client.search_read(
                    "account.move.line",
                    [["move_id", "=", move_id[0]]],
                    fields=["id"],
                    limit=200,
                )
                move_linked = len(move_lines)
            row["reference"] = row.get("payment_ref") or row.get("ref") or ""
            row["move_line_count"] = move_linked
        return lines

    def get_journal_balance(self, journal: dict, period: str) -> float:
        start = f"{period}-01"
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        if start_dt.month == 12:
            end = f"{start_dt.year + 1}-01-01"
        else:
            end = f"{start_dt.year}-{start_dt.month + 1:02d}-01"
        lines = self.client.search_read(
            "account.move.line",
            [
                ["journal_id", "=", journal["id"]],
                ["date", ">=", start],
                ["date", "<", end],
                ["parent_state", "=", "posted"],
            ],
            fields=["balance"],
            limit=5000,
        )
        return float(sum(float(row.get("balance", 0.0)) for row in lines))

    def get_vat_tax_lines(self, period: str, vat_type: str) -> list[dict]:
        start = f"{period}-01"
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        if start_dt.month == 12:
            end = f"{start_dt.year + 1}-01-01"
        else:
            end = f"{start_dt.year}-{start_dt.month + 1:02d}-01"

        tax_use = "purchase" if vat_type == "input" else "sale"
        lines = self.client.search_read(
            "account.move.line",
            [
                ["date", ">=", start],
                ["date", "<", end],
                ["parent_state", "=", "posted"],
                ["tax_line_id", "!=", False],
                ["tax_line_id.type_tax_use", "=", tax_use],
            ],
            fields=["id", "date", "balance", "move_id", "ref", "name", "tax_line_id", "move_type"],
            limit=10000,
            order="date asc,id asc",
        )
        normalized = []
        for row in lines:
            move_ref = ""
            if isinstance(row.get("move_id"), list) and row["move_id"]:
                move_ref = row["move_id"][1]
            normalized.append(
                {
                    "period": period,
                    "tax_type": vat_type,
                    "vat_amount": round(abs(float(row.get("balance", 0.0))), 2),
                    "document_ref": row.get("ref") or move_ref or row.get("name", ""),
                    "move_type": row.get("move_type", ""),
                    "source_period": period,
                    "exception_hint": "",
                    "notes": "Live extraction from posted Odoo tax lines.",
                }
            )
        return normalized

    def get_vat_control_balance(self, period: str) -> dict:
        start = f"{period}-01"
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        if start_dt.month == 12:
            end = f"{start_dt.year + 1}-01-01"
        else:
            end = f"{start_dt.year}-{start_dt.month + 1:02d}-01"

        lines = self.client.search_read(
            "account.move.line",
            [
                ["date", ">=", start],
                ["date", "<", end],
                ["parent_state", "=", "posted"],
                ["tax_line_id", "!=", False],
            ],
            fields=["balance"],
            limit=10000,
        )
        balances = [float(x.get("balance", 0.0)) for x in lines]
        return {
            "opening_balance": 0.0,
            "debits": round(sum(x for x in balances if x < 0), 2),
            "credits": round(sum(x for x in balances if x >= 0), 2),
            "closing_balance": round(sum(balances), 2),
            "assumption": "Best-effort VAT control uses posted tax line balances when dedicated control account mapping is unavailable.",
        }
