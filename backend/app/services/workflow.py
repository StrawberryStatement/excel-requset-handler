from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from backend.app.models import PmAnalysis, WorkbookConfig, WorkflowResult
from backend.app.services.diff_engine import analyze_pm_table
from backend.app.services.excel_io import (
    load_excel_table,
    write_diff_report,
    write_sync_plan_json,
    write_sync_plan_workbook,
    write_table,
)
from backend.app.services.merge_engine import build_master_rows, master_headers, master_rows_as_dicts
from backend.app.services.sync_planner import build_sync_comments


def run_excel_workflow(
    baseline_path: Path,
    pm_paths: list[Path],
    output_root: Path,
    config: WorkbookConfig | None = None,
) -> WorkflowResult:
    config = config or WorkbookConfig()
    job_id = uuid.uuid4().hex[:12]
    job_dir = output_root / job_id
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_baseline = input_dir / baseline_path.name
    shutil.copy2(baseline_path, saved_baseline)
    saved_pm_paths: list[Path] = []
    for path in pm_paths:
        target = input_dir / path.name
        shutil.copy2(path, target)
        saved_pm_paths.append(target)

    baseline = load_excel_table(saved_baseline)
    _validate_required_columns(baseline.headers, [config.fe_column], saved_baseline.name)
    _validate_unique_baseline_keys(baseline, config.fe_column)

    pm_tables = [load_excel_table(path) for path in saved_pm_paths]
    for pm_table in pm_tables:
        _validate_required_columns(pm_table.headers, [config.fe_column], pm_table.source_name)

    analyses = [analyze_pm_table(baseline, pm_table, config) for pm_table in pm_tables]

    master_rows = build_master_rows(baseline, analyses, config)
    master_path = output_dir / "quarterly_master.xlsx"
    write_table(
        master_path,
        "quarterly_master",
        master_headers(baseline, master_rows),
        master_rows_as_dicts(master_rows),
    )

    diff_report_path = output_dir / "diff_report.xlsx"
    write_diff_report(diff_report_path, analyses)

    sync_comments = build_sync_comments(baseline, analyses, config)
    sync_plan_json_path = output_dir / "sync_plan.json"
    sync_plan_workbook_path = output_dir / "sync_plan.xlsx"
    write_sync_plan_json(sync_plan_json_path, sync_comments)
    write_sync_plan_workbook(sync_plan_workbook_path, sync_comments)
    _write_job_summary(
        path=output_dir / "job_summary.json",
        job_id=job_id,
        baseline_name=saved_baseline.name,
        pm_names=[path.name for path in saved_pm_paths],
        analyses=analyses,
        sync_comment_count=len(sync_comments),
    )

    return WorkflowResult(
        job_id=job_id,
        output_dir=output_dir,
        diff_report_path=diff_report_path,
        master_workbook_path=master_path,
        sync_plan_json_path=sync_plan_json_path,
        sync_plan_workbook_path=sync_plan_workbook_path,
        analyses=analyses,
        sync_comments=sync_comments,
    )


def _write_job_summary(
    path: Path,
    job_id: str,
    baseline_name: str,
    pm_names: list[str],
    analyses: list[PmAnalysis],
    sync_comment_count: int,
) -> None:
    payload = {
        "job_id": job_id,
        "baseline_file": baseline_name,
        "pm_files": pm_names,
        "pm_file_count": len(pm_names),
        "baseline_change_count": sum(len(item.changed_baseline_fields) for item in analyses),
        "issue_count": sum(len(item.issues) for item in analyses),
        "sync_comment_count": sync_comment_count,
        "outputs": {
            "master": "quarterly_master.xlsx",
            "diff_report": "diff_report.xlsx",
            "sync_plan_xlsx": "sync_plan.xlsx",
            "sync_plan_json": "sync_plan.json",
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _validate_required_columns(headers: list[str], required_columns: list[str], source_name: str) -> None:
    missing = [column for column in required_columns if column not in headers]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{source_name} missing required columns: {joined}")


def _validate_unique_baseline_keys(baseline, key_column: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for row in baseline.records:
        raw_value = row.get(key_column)
        if raw_value is None:
            continue
        key = str(raw_value).strip()
        if not key:
            continue
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)

    if duplicates:
        joined = ", ".join(duplicates)
        raise ValueError(f"Duplicate baseline FE values: {joined}")
