import json

from finance_ai_pack.rules.month_end_gating import AMBER, GREEN, RED, can_proceed, evaluate


def test_month_end_gating_statuses(tmp_path):
    assert evaluate(0, 0) == GREEN
    assert evaluate(1, 0) == AMBER
    assert evaluate(6, 0) == RED


def test_red_requires_override(tmp_path):
    overrides = tmp_path / "overrides.json"
    overrides.write_text(json.dumps([]))
    assert can_proceed(RED, overrides) is False
    overrides.write_text(json.dumps([{"approver": "CFO"}]))
    assert can_proceed(RED, overrides) is True
