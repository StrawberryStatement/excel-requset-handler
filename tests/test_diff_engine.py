from __future__ import annotations

from backend.app.models import WorkbookConfig
from backend.app.services.diff_engine import analyze_pm_table
from backend.app.services.excel_io import load_excel_table
from tests.conftest import CONCLUSION, FE, OWNER, RISK, SCHEDULE, STATUS, UPDATED_AT, write_workbook


def test_diff_detects_extension_columns_and_baseline_changes(tmp_path, baseline_headers, baseline_rows) -> None:
    baseline_path = tmp_path / "baseline.xlsx"
    pm_path = tmp_path / "pm_alpha.xlsx"
    write_workbook(baseline_path, baseline_headers, baseline_rows)
    write_workbook(
        pm_path,
        baseline_headers + [RISK, CONCLUSION],
        [["FE-1", "RR-1", "A", "Login polish", "Doing", "2026Q2", "Dev A", "2026-05-09", "Gateway dependency", "Align in meeting"]],
    )

    analysis = analyze_pm_table(load_excel_table(baseline_path), load_excel_table(pm_path), WorkbookConfig())

    assert analysis.extension_columns == [RISK, CONCLUSION]
    changed_fields = {(item.fe_id, item.field) for item in analysis.changed_baseline_fields}
    assert ("FE-1", STATUS) in changed_fields
    assert ("FE-1", UPDATED_AT) not in changed_fields


def test_diff_reports_missing_duplicate_and_unknown_fe(tmp_path, baseline_headers, baseline_rows) -> None:
    baseline_path = tmp_path / "baseline.xlsx"
    pm_path = tmp_path / "pm_beta.xlsx"
    write_workbook(baseline_path, baseline_headers, baseline_rows)
    write_workbook(
        pm_path,
        baseline_headers,
        [
            [None, "RR-X", "A", "No key", "Review", "2026Q2", "Dev A", "2026-05-01"],
            ["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "2026-05-01"],
            ["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "2026-05-01"],
            ["FE-404", "RR-404", "Z", "Unknown", "Review", "2026Q2", "Dev Z", "2026-05-01"],
        ],
    )

    analysis = analyze_pm_table(load_excel_table(baseline_path), load_excel_table(pm_path), WorkbookConfig())

    messages = [issue.message for issue in analysis.issues]
    assert any("Missing required key" in message for message in messages)
    assert any("Duplicate FE id" in message for message in messages)
    assert any("not in the baseline" in message for message in messages)
