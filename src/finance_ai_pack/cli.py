from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from finance_ai_pack.config import Settings
from finance_ai_pack.outputs.writers import write_csv, write_html, write_json, write_xlsx
from finance_ai_pack.recon.bank.service import reconcile as bank_reconcile
from finance_ai_pack.rules.month_end_gating import can_proceed, evaluate

BASE_DIR = Path(__file__).resolve().parents[2]
FIXTURES = BASE_DIR / "fixtures"
OUTPUTS_DIR = BASE_DIR / "outputs"
OVERRIDES_FILE = FIXTURES / "overrides" / "month_end_overrides.json"

PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_period(period: str) -> str:
    if not PERIOD_PATTERN.match(period):
        raise ValueError("period must be in YYYY-MM format")
    return period


def _artifact_prefix(command: str, period: str) -> Path:
    return OUTPUTS_DIR / f"{command}_{period}"


def run_bank_recon(period: str, settings: Settings | None = None) -> dict:
    validate_period(period)
    settings = settings or Settings.from_env()
    result = bank_reconcile(period=period, fixtures_dir=FIXTURES, settings=settings)
    result.update(
        {
            "command": "bank_recon",
            "auto_posting": False,
            "notes": "No PDF parsing in v1; statement lines only.",
        }
    )

    prefix = _artifact_prefix("bank_recon", period)
    rows = [
        {
            "period": period,
            "bank": bank["display_name"],
            "journal": bank["journal"],
            "currency": bank["currency"],
            "line_count": bank["statement_line_count"],
            "reconciled_count": bank["reconciled_count"],
            "reconciled_pct": bank["reconciled_pct"],
            "difference": bank["tie_out"]["difference"],
        }
        for bank in result["banks"]
    ]
    write_json(result, prefix.with_suffix(".json"))
    write_csv(rows, prefix.with_suffix(".csv"))
    write_xlsx(rows, prefix.with_suffix(".xlsx"))
    write_html(
        title=f"Bank Reconciliation {period}",
        sections={"Summary": result.get("bank_controls_rollup", {}), "Banks": result.get("banks", [])},
        output_file=prefix.with_suffix(".html"),
    )
    result["artifacts"] = {
        "json": str(prefix.with_suffix(".json")),
        "csv": str(prefix.with_suffix(".csv")),
        "xlsx": str(prefix.with_suffix(".xlsx")),
        "html": str(prefix.with_suffix(".html")),
    }
    return result


def run_vat_pack(period: str) -> dict:
    validate_period(period)
    return {
        "command": "vat_pack",
        "period": period,
        "mode": "fixture-only",
        "auto_posting": False,
        "status": "proposal-generated",
    }


def run_month_end(period: str, settings: Settings | None = None) -> dict:
    validate_period(period)
    settings = settings or Settings.from_env()
    bank = run_bank_recon(period, settings=settings)
    rollup = bank["bank_controls_rollup"]
    unmatched_transactions = rollup["total_statement_lines"] - rollup["total_reconciled_lines"]
    unexplained_amount = float(sum(abs(b["tie_out"]["difference"]) for b in bank["banks"]))
    status = evaluate(unmatched_transactions=unmatched_transactions, unexplained_amount=unexplained_amount)
    proceed = can_proceed(status=status, overrides_file=OVERRIDES_FILE)
    return {
        "command": "month_end",
        "period": period,
        "mode": bank["mode"],
        "auto_posting": False,
        "status": status,
        "proceed": proceed,
        "bank_controls_rollup": rollup,
    }


def main() -> None:
    settings = Settings.from_env()

    parser = argparse.ArgumentParser(prog="run")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for cmd in ("bank_recon", "vat_pack", "month_end"):
        sub = subparsers.add_parser(cmd)
        sub.add_argument("--period", required=True)

    args = parser.parse_args()

    if args.command == "bank_recon":
        payload = run_bank_recon(args.period, settings=settings)
    elif args.command == "vat_pack":
        payload = run_vat_pack(args.period)
    else:
        payload = run_month_end(args.period, settings=settings)

    print(json.dumps(payload, indent=2))
    print("no auto-posting performed")


if __name__ == "__main__":
    main()
