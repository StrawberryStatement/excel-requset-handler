from __future__ import annotations

from backend.app.models import WorkbookConfig
from backend.app.services.diff_engine import analyze_pm_table
from backend.app.services.excel_io import load_excel_table
from backend.app.services.sync_planner import build_sync_comments
from tests.conftest import CONCLUSION, CUSTOMER_IMPACT, FE, RISK, write_workbook


def test_sync_planner_converts_extensions_to_comment_blocks(tmp_path, baseline_headers, baseline_rows) -> None:
    baseline_path = tmp_path / "baseline.xlsx"
    pm_a_path = tmp_path / "pm_a.xlsx"
    pm_b_path = tmp_path / "pm_b.xlsx"
    write_workbook(baseline_path, baseline_headers, baseline_rows)
    write_workbook(
        pm_a_path,
        baseline_headers + [RISK],
        [["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "2026-05-01", "Gateway dependency"]],
    )
    write_workbook(
        pm_b_path,
        baseline_headers + [CUSTOMER_IMPACT],
        [["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "2026-05-01", "Affects customer A"]],
    )
    baseline = load_excel_table(baseline_path)
    analyses = [
        analyze_pm_table(baseline, load_excel_table(pm_a_path), WorkbookConfig()),
        analyze_pm_table(baseline, load_excel_table(pm_b_path), WorkbookConfig()),
    ]

    comments = build_sync_comments(baseline, analyses, WorkbookConfig())

    assert len(comments) == 1
    assert comments[0].fe_id == "FE-1"
    assert "[pm_a]" in comments[0].comment
    assert "[pm_b]" in comments[0].comment
    assert RISK in comments[0].comment
    assert CUSTOMER_IMPACT in comments[0].comment


def test_sync_planner_skips_rows_without_extension_values(tmp_path, baseline_headers, baseline_rows) -> None:
    baseline_path = tmp_path / "baseline.xlsx"
    pm_path = tmp_path / "pm_empty.xlsx"
    write_workbook(baseline_path, baseline_headers, baseline_rows)
    write_workbook(
        pm_path,
        baseline_headers + [CONCLUSION],
        [["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "2026-05-01", ""]],
    )
    baseline = load_excel_table(baseline_path)
    analysis = analyze_pm_table(baseline, load_excel_table(pm_path), WorkbookConfig())

    comments = build_sync_comments(baseline, [analysis], WorkbookConfig())

    assert comments == []
