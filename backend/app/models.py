from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


CellValue = str | int | float | bool | None

DEFAULT_FE_COLUMN = "FE\u7f16\u53f7"
DEFAULT_RR_COLUMN = "RR\u7f16\u53f7"
DEFAULT_TITLE_COLUMN = "\u9700\u6c42\u6807\u9898"
DEFAULT_SERVICE_COLUMN = "\u4e91\u670d\u52a1"
DEFAULT_STATUS = "\u5f85\u786e\u8ba4"


@dataclass(frozen=True)
class WorkbookConfig:
    fe_column: str = DEFAULT_FE_COLUMN
    rr_column: str = DEFAULT_RR_COLUMN
    title_column: str = DEFAULT_TITLE_COLUMN
    service_column: str = DEFAULT_SERVICE_COLUMN
    comment_columns: tuple[str, ...] = (
        "\u72b6\u6001",
        "\u6392\u671f",
        "\u8d1f\u8d23\u4eba",
        "\u4f18\u5148\u7ea7",
        "\u5907\u6ce8",
    )
    ignored_compare_columns: tuple[str, ...] = (
        "\u6700\u540e\u66f4\u65b0\u65f6\u95f4",
        "\u66f4\u65b0\u65f6\u95f4",
    )


@dataclass
class ExcelTable:
    source_name: str
    sheet_name: str
    headers: list[str]
    records: list[dict[str, CellValue]]

    def by_key(self, key_column: str) -> dict[str, dict[str, CellValue]]:
        keyed: dict[str, dict[str, CellValue]] = {}
        for row in self.records:
            raw_key = row.get(key_column)
            if raw_key is None:
                continue
            key = str(raw_key).strip()
            if key:
                keyed[key] = row
        return keyed


@dataclass
class FieldChange:
    fe_id: str
    field: str
    baseline_value: CellValue
    pm_value: CellValue
    source_name: str


@dataclass
class RowIssue:
    level: str
    fe_id: str | None
    message: str
    source_name: str
    row_number: int | None = None


@dataclass
class PmAnalysis:
    source_name: str
    pm_table: ExcelTable
    extension_columns: list[str] = field(default_factory=list)
    changed_baseline_fields: list[FieldChange] = field(default_factory=list)
    issues: list[RowIssue] = field(default_factory=list)


@dataclass
class MasterRow:
    fe_id: str
    values: dict[str, CellValue]
    source_names: list[str] = field(default_factory=list)
    extension_values: dict[str, CellValue] = field(default_factory=dict)


@dataclass
class SyncComment:
    fe_id: str
    title: str
    comment: str
    source_names: list[str]
    status: str = DEFAULT_STATUS


@dataclass
class WorkflowResult:
    job_id: str
    output_dir: Path
    diff_report_path: Path
    master_workbook_path: Path
    sync_plan_json_path: Path
    sync_plan_workbook_path: Path
    analyses: list[PmAnalysis]
    sync_comments: list[SyncComment]
