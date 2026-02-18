import os
from pathlib import Path

import pytest

from finance_ai_pack.config import Settings
from finance_ai_pack.recon.bank.service import reconcile


requires_live = pytest.mark.skipif(
    not (os.getenv("LIVE_ODOO") == "1" and os.getenv("FIXTURE_MODE", "true").lower() == "false"),
    reason="Live Odoo integration tests are opt-in only (LIVE_ODOO=1 and FIXTURE_MODE=false).",
)


@requires_live
def test_live_odoo_discovery_and_rollup():
    settings = Settings.from_env()
    payload = reconcile(period="2025-01", fixtures_dir=Path("fixtures"), settings=settings)
    assert payload["mode"] == "live-odoo"
    assert "bank_controls_rollup" in payload
    assert payload["bank_controls_rollup"]["bank_count"] >= 1
