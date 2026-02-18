import pytest

from finance_ai_pack.cli import validate_period


def test_validate_period_ok():
    assert validate_period("2025-01") == "2025-01"


def test_validate_period_bad():
    with pytest.raises(ValueError):
        validate_period("2025-13")
