from __future__ import annotations

from backend.app.models import ExcelTable, FieldChange, PmAnalysis, RowIssue, WorkbookConfig
from backend.app.services.excel_io import normalize_cell


def analyze_pm_table(baseline: ExcelTable, pm_table: ExcelTable, config: WorkbookConfig) -> PmAnalysis:
    baseline_by_fe = baseline.by_key(config.fe_column)
    baseline_headers = set(baseline.headers)
    pm_headers = set(pm_table.headers)

    extension_columns = [header for header in pm_table.headers if header not in baseline_headers]
    ignored_columns = {config.fe_column, *config.ignored_compare_columns}
    comparable_columns = [
        header
        for header in baseline.headers
        if header in pm_headers and header not in ignored_columns
    ]

    analysis = PmAnalysis(
        source_name=pm_table.source_name,
        pm_table=pm_table,
        extension_columns=extension_columns,
    )

    seen_fe_ids: set[str] = set()
    for index, pm_row in enumerate(pm_table.records, start=2):
        fe_id = normalize_cell(pm_row.get(config.fe_column))
        if not fe_id:
            analysis.issues.append(RowIssue(
                level="error",
                fe_id=None,
                message=f"Missing required key column: {config.fe_column}",
                source_name=pm_table.source_name,
                row_number=index,
            ))
            continue

        if fe_id in seen_fe_ids:
            analysis.issues.append(RowIssue(
                level="warning",
                fe_id=fe_id,
                message="Duplicate FE id in one PM file",
                source_name=pm_table.source_name,
                row_number=index,
            ))
        seen_fe_ids.add(fe_id)

        baseline_row = baseline_by_fe.get(fe_id)
        if baseline_row is None:
            analysis.issues.append(RowIssue(
                level="warning",
                fe_id=fe_id,
                message="PM file contains an FE id that is not in the baseline",
                source_name=pm_table.source_name,
                row_number=index,
            ))
            continue

        for field in comparable_columns:
            baseline_value = baseline_row.get(field)
            pm_value = pm_row.get(field)
            if normalize_cell(baseline_value) != normalize_cell(pm_value):
                analysis.changed_baseline_fields.append(FieldChange(
                    fe_id=fe_id,
                    field=field,
                    baseline_value=baseline_value,
                    pm_value=pm_value,
                    source_name=pm_table.source_name,
                ))

    return analysis
