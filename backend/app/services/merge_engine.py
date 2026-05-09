from __future__ import annotations

from backend.app.models import CellValue, ExcelTable, MasterRow, PmAnalysis, WorkbookConfig
from backend.app.services.excel_io import normalize_cell


SOURCE_PM_COLUMN = "\u6765\u6e90PM\u6587\u4ef6"


def build_master_rows(
    baseline: ExcelTable,
    analyses: list[PmAnalysis],
    config: WorkbookConfig,
) -> list[MasterRow]:
    baseline_by_fe = baseline.by_key(config.fe_column)
    master_by_fe: dict[str, MasterRow] = {}

    for fe_id, baseline_row in baseline_by_fe.items():
        master_by_fe[fe_id] = MasterRow(
            fe_id=fe_id,
            values=dict(baseline_row),
        )

    for analysis in analyses:
        for pm_row in analysis.pm_table.records:
            fe_id = normalize_cell(pm_row.get(config.fe_column))
            if not fe_id:
                continue

            master_row = master_by_fe.get(fe_id)
            if master_row is None:
                master_row = MasterRow(fe_id=fe_id, values=dict(pm_row))
                master_by_fe[fe_id] = master_row

            if analysis.source_name not in master_row.source_names:
                master_row.source_names.append(analysis.source_name)

            for column in analysis.extension_columns:
                value = pm_row.get(column)
                if normalize_cell(value):
                    prefixed_column = f"{analysis.source_name}__{column}"
                    master_row.extension_values[prefixed_column] = value

    return list(master_by_fe.values())


def master_headers(baseline: ExcelTable, master_rows: list[MasterRow]) -> list[str]:
    extension_headers: list[str] = []
    for row in master_rows:
        for column in row.extension_values:
            if column not in extension_headers:
                extension_headers.append(column)

    return baseline.headers + [SOURCE_PM_COLUMN] + extension_headers


def master_rows_as_dicts(master_rows: list[MasterRow]) -> list[dict[str, CellValue]]:
    rows: list[dict[str, CellValue]] = []
    for row in master_rows:
        values = dict(row.values)
        values[SOURCE_PM_COLUMN] = ", ".join(row.source_names)
        values.update(row.extension_values)
        rows.append(values)
    return rows

