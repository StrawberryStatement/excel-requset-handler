from __future__ import annotations

import tempfile
import json
import re
from zipfile import BadZipFile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openpyxl.utils.exceptions import InvalidFileException

from backend.app.commenting.schemas import DEFAULT_COMMENT_TEMPLATE
from backend.app.models import DEFAULT_FE_COLUMN, DEFAULT_RR_COLUMN, DEFAULT_SERVICE_COLUMN, DEFAULT_TITLE_COLUMN, WorkbookConfig
from backend.app.services.v2_workflow import V2WorkflowConfig, run_v2_workflow


PROJECT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_DIR / "frontend"
JOBS_DIR = PROJECT_DIR / "jobs"

app = FastAPI(title="RR-FE Excel Workspace", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/jobs")
async def create_job(
    baseline: UploadFile = File(...),
    pm_files: list[UploadFile] = File(...),
    fe_column: str = Form(DEFAULT_FE_COLUMN),
    rr_column: str = Form(DEFAULT_RR_COLUMN),
    service_column: str = Form(DEFAULT_SERVICE_COLUMN),
    title_column: str = Form(DEFAULT_TITLE_COLUMN),
    owned_services: str = Form(""),
    comment_fields: str = Form(""),
    comment_template: str = Form(DEFAULT_COMMENT_TEMPLATE),
    comment_target: str = Form("both"),
    sync_linked: str = Form("false"),
    fill_defaults_json: str = Form("{}"),
) -> dict:
    if not baseline.filename:
        raise HTTPException(status_code=400, detail="Missing baseline file name")
    if not pm_files:
        raise HTTPException(status_code=400, detail="At least one PM file is required")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        baseline_path = tmp_dir / _safe_upload_filename(baseline.filename, "baseline.xlsx")
        baseline_path.write_bytes(await baseline.read())

        pm_paths: list[Path] = []
        for index, pm_file in enumerate(pm_files, start=1):
            if not pm_file.filename:
                continue
            path = tmp_dir / _safe_upload_filename(pm_file.filename, f"source_{index}.xlsx")
            path.write_bytes(await pm_file.read())
            pm_paths.append(path)

        if not pm_paths:
            raise HTTPException(status_code=400, detail="No valid PM files were uploaded")

        try:
            result = run_v2_workflow(
                baseline_path=baseline_path,
                source_paths=pm_paths,
                output_root=JOBS_DIR,
                config=V2WorkflowConfig(
                    workbook=WorkbookConfig(
                        fe_column=fe_column.strip() or DEFAULT_FE_COLUMN,
                        rr_column=rr_column.strip() or DEFAULT_RR_COLUMN,
                        service_column=service_column.strip() or DEFAULT_SERVICE_COLUMN,
                        title_column=title_column.strip() or DEFAULT_TITLE_COLUMN,
                    ),
                    owned_services=tuple(_split_csv(owned_services)),
                    comment_fields=tuple(_split_csv(comment_fields)),
                    comment_template=comment_template or DEFAULT_COMMENT_TEMPLATE,
                    comment_target=comment_target if comment_target in {"fe", "rr", "both"} else "both",
                    sync_linked=sync_linked.lower() in {"true", "1", "yes", "on"},
                    fill_defaults=_parse_fill_defaults(fill_defaults_json),
                ),
            )
        except (BadZipFile, InvalidFileException, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = result.response_payload
    payload["summary"]["pm_file_count"] = payload["summary"]["source_list_count"]
    payload["summary"]["issue_count"] = payload["summary"]["critical_issue_count"]
    payload["summary"]["baseline_change_count"] = 0
    payload["downloads"]["diff_report"] = payload["downloads"]["package"]
    payload["downloads"]["sync_plan_xlsx"] = payload["downloads"]["package"]
    return payload


@app.get("/api/jobs/{job_id}/downloads/{file_name}")
def download_file(job_id: str, file_name: str) -> FileResponse:
    allowed = {"quarterly_master.xlsx", "diff_report.xlsx", "sync_plan.xlsx", "sync_plan.json", "\u9700\u6c42\u6c47\u603b\u5305.xlsx"}
    if file_name not in allowed:
        raise HTTPException(status_code=404, detail="Unknown output file")

    path = JOBS_DIR / job_id / "output" / file_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(path, filename=file_name)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_fill_defaults(value: str) -> dict[str, str]:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid fill defaults JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("fill_defaults_json must be an object")
    return {str(key).strip(): str(item).strip() for key, item in payload.items() if str(key).strip() and str(item).strip()}


def _safe_upload_filename(filename: str, fallback: str) -> str:
    name = Path(filename or fallback).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if not name:
        name = fallback
    if not Path(name).suffix:
        name = f"{name}.xlsx"
    return name


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
