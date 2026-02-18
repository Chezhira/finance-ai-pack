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
