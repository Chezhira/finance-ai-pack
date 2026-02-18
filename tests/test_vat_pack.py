import pytest
from pathlib import Path

from finance_ai_pack.cli import run_month_end, run_vat_pack
from finance_ai_pack.recon.vat.service import read_tra_file
from finance_ai_pack.rules.month_end_gating import AMBER, GREEN, RED, evaluate


def test_parse_tra_file():
    payload = read_tra_file(Path("fixtures/vat/tra_vat_2025-01.csv"))
    assert payload["2025-01"].input_vat == 1600.0
    assert payload["2025-02"].output_vat == 1680.0


def test_vat_pack_monthly_comparison_and_artifacts():
    payload = run_vat_pack(period_from="2025-01", period_to="2025-02")
    assert payload["command"] == "vat_pack"
    assert len(payload["monthly_summary"]) == 2
    jan = [x for x in payload["monthly_summary"] if x["period"] == "2025-01"][0]
    assert jan["odoo_input_vat"] == 1700.0
    assert jan["tra_input_vat"] == 1600.0
    assert jan["input_difference"] == 100.0
    for artifact in payload["artifacts"].values():
        assert Path(artifact).exists()


def test_exception_categorization_for_timing_credit_missing_document():
    payload = run_vat_pack(period_from="2025-01", period_to="2025-01")
    categories = {row["category"] for row in payload["exception_register"]}
    assert "timing/posting period" in categories
    assert "credit_notes/reversals" in categories
    assert "missing documents" in categories


def test_gating_status_changes_with_vat_thresholds(tmp_path):
    assert evaluate(0, 0, [0]) == GREEN
    assert evaluate(0, 0, [25]) == AMBER
    assert evaluate(0, 0, [300]) == RED

    overrides = tmp_path / "overrides.json"
    overrides.write_text("[]")

    payload = run_month_end("2025-01")
    assert payload["status"] in {GREEN, AMBER, RED}


def test_parse_tra_xlsx_file(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["period", "input_vat", "output_vat"])
    ws.append(["2025-01", 100.0, 200.0])
    ws.append(["2025-02", 300.0, 400.0])
    tra = tmp_path / "tra.xlsx"
    wb.save(tra)

    payload = read_tra_file(tra)
    assert payload["2025-01"].input_vat == 100.0
    assert payload["2025-02"].output_vat == 400.0


def test_reject_unsupported_tra_extension(tmp_path):
    file = tmp_path / "tra.txt"
    file.write_text("period,input_vat,output_vat\n2025-01,10,20\n")
    with pytest.raises(ValueError, match=r"\.csv or \.xlsx"):
        read_tra_file(file)


def test_reject_missing_required_tra_columns(tmp_path):
    file = tmp_path / "tra.csv"
    file.write_text("period,input_vat\n2025-01,10\n")
    with pytest.raises(ValueError, match="period,input_vat,output_vat"):
        read_tra_file(file)
