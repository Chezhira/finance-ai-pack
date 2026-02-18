from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import json

from finance_ai_pack.config import Settings
from finance_ai_pack.connectors.odoo.client import OdooClient
from finance_ai_pack.connectors.odoo.fixtures_adapter import FixturesAdapter
from finance_ai_pack.connectors.odoo.live_adapter import LiveOdooAdapter


@dataclass
class BankProfile:
    code: str
    display_name: str
    currency: str


def _end_of_month(period: str) -> date:
    start = datetime.strptime(f"{period}-01", "%Y-%m-%d").date()
    if start.month == 12:
        return date(start.year + 1, 1, 1)
    return date(start.year, start.month + 1, 1)


def _line_aging_bucket(line_date: str | None, period: str) -> str:
    if not line_date:
        return "unknown"
    cutoff = _end_of_month(period)
    txn_date = datetime.strptime(line_date, "%Y-%m-%d").date()
    age_days = (cutoff - txn_date).days
    if age_days <= 30:
        return "0_30"
    if age_days <= 60:
        return "31_60"
    return "61_plus"


def _load_registry(registry_file: Path) -> dict:
    if not registry_file.exists():
        return {"default_profile": {"code": "default", "display_name": "Default", "currency": ""}, "profiles": {}}
    payload = json.loads(registry_file.read_text() or "{}")
    return payload


def _profile_for_journal(journal_name: str, journal_currency: str, registry: dict) -> BankProfile:
    profiles = registry.get("profiles", {})
    aliases = registry.get("journal_name_map", {})
    key = aliases.get(journal_name, journal_name)
    candidate = profiles.get(key)
    if candidate:
        return BankProfile(
            code=candidate.get("code", key.lower().replace(" ", "_")),
            display_name=candidate.get("display_name", key),
            currency=candidate.get("currency", journal_currency),
        )
    default = registry.get("default_profile", {})
    fallback_code = f"journal_{journal_name.lower().replace(' ', '_')}"
    return BankProfile(
        code=default.get("code", fallback_code),
        display_name=journal_name,
        currency=journal_currency or default.get("currency", ""),
    )


def _build_adapter(settings: Settings, fixtures_dir: Path):
    if settings.fixture_mode:
        return FixturesAdapter(fixtures_dir)
    return LiveOdooAdapter(OdooClient(settings))


def reconcile(period: str, fixtures_dir: Path, settings: Settings | None = None) -> dict:
    settings = settings or Settings.from_env()
    adapter = _build_adapter(settings, fixtures_dir)
    registry = _load_registry(Path(__file__).resolve().parents[2] / "rules" / "bank_registry.yml")

    journals = adapter.discover_bank_journals()
    banks = []
    total_lines = 0
    total_reconciled = 0
    all_exceptions: list[dict] = []

    for journal in journals:
        profile = _profile_for_journal(journal["name"], journal.get("currency", ""), registry)
        lines = adapter.get_statement_lines(journal, period)
        reconciled_count = sum(1 for line in lines if line.get("is_reconciled"))
        unreconciled = [line for line in lines if not line.get("is_reconciled")]

        aging = {"0_30": 0, "31_60": 0, "61_plus": 0, "unknown": 0}
        for line in unreconciled:
            aging[_line_aging_bucket(line.get("date"), period)] += 1

        statement_ending_balance = float(sum(float(line.get("amount", 0.0)) for line in lines))
        ledger_balance = float(adapter.get_journal_balance(journal, period))

        exceptions = []
        if unreconciled:
            exceptions.append(
                {
                    "type": "UNRECONCILED_LINES",
                    "message": f"{len(unreconciled)} unreconciled statement lines.",
                    "sample_refs": [line.get("reference") for line in unreconciled[:5]],
                }
            )
        if abs(statement_ending_balance - ledger_balance) > 0.01:
            exceptions.append(
                {
                    "type": "TIE_OUT_DIFFERENCE",
                    "message": "Statement vs ledger tie-out difference exceeds tolerance.",
                    "difference": round(statement_ending_balance - ledger_balance, 2),
                }
            )

        bank_payload = {
            "code": profile.code,
            "display_name": profile.display_name,
            "journal": journal["name"],
            "journal_id": journal["id"],
            "journal_type": journal.get("type", "bank"),
            "currency": profile.currency,
            "statement_line_count": len(lines),
            "reconciled_count": reconciled_count,
            "reconciled_pct": round((reconciled_count / len(lines) * 100) if lines else 100.0, 2),
            "unreconciled_aging_buckets": aging,
            "exceptions": exceptions,
            "tie_out": {
                "statement_ending_balance": statement_ending_balance,
                "ledger_balance": ledger_balance,
                "difference": round(statement_ending_balance - ledger_balance, 2),
                "assumption": "Best-effort tie-out uses sum of statement line amounts vs posted journal move-line balances for the period.",
            },
        }
        banks.append(bank_payload)
        all_exceptions.extend({"bank": profile.display_name, **item} for item in exceptions)
        total_lines += len(lines)
        total_reconciled += reconciled_count

    rollup = {
        "bank_count": len(banks),
        "total_statement_lines": total_lines,
        "total_reconciled_lines": total_reconciled,
        "overall_reconciled_pct": round((total_reconciled / total_lines * 100) if total_lines else 100.0, 2),
        "exception_count": len(all_exceptions),
        "exceptions": all_exceptions,
    }

    return {
        "period": period,
        "mode": "fixture-only" if settings.fixture_mode else "live-odoo",
        "banks": banks,
        "proposed_journals": [journal["name"] for journal in journals],
        "exceptions": all_exceptions,
        "bank_controls_rollup": rollup,
    }
