from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from finance_ai_pack.config import Settings
from finance_ai_pack.outputs.writers import write_csv, write_html, write_json, write_xlsx
from finance_ai_pack.recon.bank.service import reconcile as bank_reconcile
from finance_ai_pack.recon.vat.service import reconcile_vat
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


def run_vat_pack(
    period_from: str,
    period_to: str | None = None,
    settings: Settings | None = None,
    tra_file: Path | None = None,
) -> dict:
    validate_period(period_from)
    period_to = period_to or period_from
    validate_period(period_to)
    settings = settings or Settings.from_env()

    result = reconcile_vat(
        period_from=period_from,
        period_to=period_to,
        fixtures_dir=FIXTURES,
        settings=settings,
        tra_file=tra_file,
    )

    prefix = OUTPUTS_DIR / "vat_monthly_summary"
    write_json({"monthly_summary": result["monthly_summary"]}, prefix.with_suffix(".json"))
    write_csv(result["monthly_summary"], prefix.with_suffix(".csv"))
    write_xlsx(result["monthly_summary"], prefix.with_suffix(".xlsx"))

    exceptions_prefix = OUTPUTS_DIR / "vat_exception_register"
    write_json({"exception_register": result["exception_register"]}, exceptions_prefix.with_suffix(".json"))
    write_csv(result["exception_register"], exceptions_prefix.with_suffix(".csv"))
    write_xlsx(result["exception_register"], exceptions_prefix.with_suffix(".xlsx"))

    report_file = OUTPUTS_DIR / "vat_pack_report.html"
    write_html(
        title=f"VAT Pack {period_from} to {period_to}",
        sections={
            "Narrative": {"text": result["narrative"]},
            "Monthly Summary": result["monthly_summary"],
            "Exception Register": result["exception_register"],
        },
        output_file=report_file,
    )

    result["artifacts"] = {
        "vat_monthly_summary_json": str(prefix.with_suffix(".json")),
        "vat_monthly_summary_csv": str(prefix.with_suffix(".csv")),
        "vat_monthly_summary_xlsx": str(prefix.with_suffix(".xlsx")),
        "vat_exception_register_json": str(exceptions_prefix.with_suffix(".json")),
        "vat_exception_register_csv": str(exceptions_prefix.with_suffix(".csv")),
        "vat_exception_register_xlsx": str(exceptions_prefix.with_suffix(".xlsx")),
        "vat_pack_report_html": str(report_file),
    }
    return result


def run_month_end(period: str, settings: Settings | None = None, tra_file: Path | None = None) -> dict:
    validate_period(period)
    settings = settings or Settings.from_env()
    bank = run_bank_recon(period, settings=settings)
    vat = run_vat_pack(period_from=period, period_to=period, settings=settings, tra_file=tra_file)

    rollup = bank["bank_controls_rollup"]
    unmatched_transactions = rollup["total_statement_lines"] - rollup["total_reconciled_lines"]
    unexplained_amount = float(sum(abs(b["tie_out"]["difference"]) for b in bank["banks"]))
    vat_monthly_differences = [abs(float(row["net_vat_difference"])) for row in vat["monthly_summary"]]

    status = evaluate(
        unmatched_transactions=unmatched_transactions,
        unexplained_amount=unexplained_amount,
        vat_monthly_differences=vat_monthly_differences,
    )
    proceed = can_proceed(status=status, overrides_file=OVERRIDES_FILE)
    return {
        "command": "month_end",
        "period": period,
        "mode": bank["mode"],
        "auto_posting": False,
        "status": status,
        "proceed": proceed,
        "bank_controls_rollup": rollup,
        "vat_controls_rollup": {
            "months": len(vat["monthly_summary"]),
            "max_abs_net_vat_difference": max(vat_monthly_differences) if vat_monthly_differences else 0.0,
            "exception_count": len(vat["exception_register"]),
        },
    }


def main() -> None:
    settings = Settings.from_env()

    parser = argparse.ArgumentParser(prog="run")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bank_sub = subparsers.add_parser("bank_recon")
    bank_sub.add_argument("--period", required=True)

    vat_sub = subparsers.add_parser("vat_pack")
    vat_sub.add_argument("--period_from", required=True)
    vat_sub.add_argument("--period_to")
    vat_sub.add_argument("--tra_file")

    month_end_sub = subparsers.add_parser("month_end")
    month_end_sub.add_argument("--period", required=True)
    month_end_sub.add_argument("--tra_file")

    args = parser.parse_args()

    if args.command == "bank_recon":
        payload = run_bank_recon(args.period, settings=settings)
    elif args.command == "vat_pack":
        payload = run_vat_pack(
            period_from=args.period_from,
            period_to=args.period_to,
            settings=settings,
            tra_file=Path(args.tra_file) if args.tra_file else None,
        )
    else:
        payload = run_month_end(
            args.period,
            settings=settings,
            tra_file=Path(args.tra_file) if args.tra_file else None,
        )

    print(json.dumps(payload, indent=2))
    print("no auto-posting performed")


if __name__ == "__main__":
    main()
