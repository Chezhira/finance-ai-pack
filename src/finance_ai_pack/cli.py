from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from finance_ai_pack.config import Settings
from finance_ai_pack.recon.bank.service import reconcile as bank_reconcile
from finance_ai_pack.rules.month_end_gating import can_proceed, evaluate

BASE_DIR = Path(__file__).resolve().parents[2]
FIXTURES = BASE_DIR / "fixtures"
OVERRIDES_FILE = FIXTURES / "overrides" / "month_end_overrides.json"

PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_period(period: str) -> str:
    if not PERIOD_PATTERN.match(period):
        raise ValueError("period must be in YYYY-MM format")
    return period


def run_bank_recon(period: str) -> dict:
    validate_period(period)
    result = bank_reconcile(period=period, fixtures_dir=FIXTURES)
    result.update(
        {
            "command": "bank_recon",
            "mode": "fixture-only",
            "auto_posting": False,
            "notes": "No PDF parsing in v1; Odoo statement line fixtures only.",
        }
    )
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


def run_month_end(period: str) -> dict:
    validate_period(period)
    # scaffold metrics intentionally deterministic for fixture-mode baseline
    status = evaluate(unmatched_transactions=2, unexplained_amount=300)
    proceed = can_proceed(status=status, overrides_file=OVERRIDES_FILE)
    return {
        "command": "month_end",
        "period": period,
        "mode": "fixture-only",
        "auto_posting": False,
        "status": status,
        "proceed": proceed,
    }


def main() -> None:
    _ = Settings.from_env()  # loaded for future live-mode support; fixture-first by default

    parser = argparse.ArgumentParser(prog="run")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for cmd in ("bank_recon", "vat_pack", "month_end"):
        sub = subparsers.add_parser(cmd)
        sub.add_argument("--period", required=True)

    args = parser.parse_args()

    if args.command == "bank_recon":
        payload = run_bank_recon(args.period)
    elif args.command == "vat_pack":
        payload = run_vat_pack(args.period)
    else:
        payload = run_month_end(args.period)

    print(json.dumps(payload, indent=2))
    print("no auto-posting performed")


if __name__ == "__main__":
    main()
