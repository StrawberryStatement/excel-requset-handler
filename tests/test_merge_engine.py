from __future__ import annotations

from backend.app.models import WorkbookConfig
from backend.app.services.diff_engine import analyze_pm_table
from backend.app.services.excel_io import load_excel_table
from backend.app.services.merge_engine import SOURCE_PM_COLUMN, build_master_rows, master_headers, master_rows_as_dicts
from tests.conftest import CONCLUSION, FE, RISK, STATUS, write_workbook


def test_merge_preserves_baseline_and_prefixes_extensions(tmp_path, baseline_headers, baseline_rows) -> None:
    baseline_path = tmp_path / "baseline.xlsx"
    pm_path = tmp_path / "pm_alpha.xlsx"
    write_workbook(baseline_path, baseline_headers, baseline_rows)
    write_workbook(
        pm_path,
        baseline_headers + [RISK, CONCLUSION],
        [["FE-1", "RR-1", "A", "Login polish", "Doing", "2026Q2", "Dev A", "2026-05-09", "Gateway", "Approved"]],
    )
    baseline = load_excel_table(baseline_path)
    analysis = analyze_pm_table(baseline, load_excel_table(pm_path), WorkbookConfig())

    rows = build_master_rows(baseline, [analysis], WorkbookConfig())
    headers = master_headers(baseline, rows)
    dict_rows = master_rows_as_dicts(rows)

    assert SOURCE_PM_COLUMN in headers
    assert "pm_alpha__" + RISK in headers
    fe_1 = next(row for row in dict_rows if row[FE] == "FE-1")
    assert fe_1[STATUS] == "Review"
    assert fe_1["pm_alpha__" + RISK] == "Gateway"
    assert fe_1[SOURCE_PM_COLUMN] == "pm_alpha"


def test_merge_includes_pm_only_fe_for_review(tmp_path, baseline_headers, baseline_rows) -> None:
    baseline_path = tmp_path / "baseline.xlsx"
    pm_path = tmp_path / "pm_gamma.xlsx"
    write_workbook(baseline_path, baseline_headers, baseline_rows)
    write_workbook(
        pm_path,
        baseline_headers + [CONCLUSION],
        [["FE-404", "RR-404", "Z", "Unknown", "Review", "2026Q4", "Dev Z", "2026-05-09", "Needs mapping"]],
    )
    baseline = load_excel_table(baseline_path)
    analysis = analyze_pm_table(baseline, load_excel_table(pm_path), WorkbookConfig())

    rows = master_rows_as_dicts(build_master_rows(baseline, [analysis], WorkbookConfig()))

    assert any(row[FE] == "FE-404" for row in rows)
