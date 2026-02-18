from pathlib import Path

from finance_ai_pack.cli import run_bank_recon, run_month_end, run_vat_pack


def test_cli_bank_command_payload():
    payload = run_bank_recon("2025-01")
    assert payload["command"] == "bank_recon"
    assert payload["mode"] == "fixture-only"
    assert payload["auto_posting"] is False
    assert "bank_controls_rollup" in payload
    for artifact in payload["artifacts"].values():
        assert Path(artifact).exists()


def test_cli_vat_command_payload():
    payload = run_vat_pack("2025-01")
    assert payload["command"] == "vat_pack"
    assert payload["mode"] == "fixture-only"


def test_cli_month_end_payload():
    payload = run_month_end("2025-01")
    assert payload["command"] == "month_end"
    assert payload["status"] in {"GREEN", "AMBER", "RED"}
    assert "bank_controls_rollup" in payload
