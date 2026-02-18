from finance_ai_pack.cli import run_bank_recon, run_month_end, run_vat_pack


def test_cli_bank_command_payload():
    payload = run_bank_recon("2025-01")
    assert payload["command"] == "bank_recon"
    assert payload["mode"] == "fixture-only"
    assert payload["auto_posting"] is False


def test_cli_vat_command_payload():
    payload = run_vat_pack(period_from="2025-01")
    assert payload["command"] == "vat_pack"
    assert payload["mode"] == "fixture-only"


def test_cli_month_end_payload():
    payload = run_month_end("2025-01")
    assert payload["command"] == "month_end"
    assert payload["status"] in {"GREEN", "AMBER", "RED"}


def test_month_end_uses_input_output_differences_for_vat_gating(monkeypatch):
    def fake_bank(period, settings=None):
        return {
            "mode": "fixture-only",
            "banks": [{"tie_out": {"difference": 0.0}}],
            "bank_controls_rollup": {"total_statement_lines": 0, "total_reconciled_lines": 0},
        }

    def fake_vat(period_from, period_to=None, settings=None, tra_file=None):
        return {
            "monthly_summary": [
                {
                    "period": "2025-01",
                    "input_difference": 500.0,
                    "output_difference": -500.0,
                    "net_vat_difference": 0.0,
                }
            ],
            "exception_register": [],
        }

    monkeypatch.setattr("finance_ai_pack.cli.run_bank_recon", fake_bank)
    monkeypatch.setattr("finance_ai_pack.cli.run_vat_pack", fake_vat)

    from finance_ai_pack.cli import run_month_end

    payload = run_month_end("2025-01")
    assert payload["vat_controls_rollup"]["max_abs_vat_difference"] == 500.0
    assert payload["status"] == "RED"
