from finance_ai_pack.cli import run_bank_recon


def test_bank_recon_includes_pilot_banks():
    payload = run_bank_recon("2025-01")
    assert {b["code"] for b in payload["banks"]} == {"nmb_tzs", "nbc_usd"}
