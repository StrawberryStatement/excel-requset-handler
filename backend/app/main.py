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
    fe_column: str | None = Form(None),
    rr_column: str | None = Form(None),
    service_column: str | None = Form(None),
    title_column: str | None = Form(None),
    owned_services: str = Form(""),
    comment_fields: str = Form(""),
    comment_template: str = Form(DEFAULT_COMMENT_TEMPLATE),
    comment_target: str = Form("both"),
    sync_linked: str = Form("false"),
    fill_defaults_json: str = Form("{}"),
) -> dict:
    fe_column_value = _resolve_required_form_value(fe_column, DEFAULT_FE_COLUMN, "FE 列名")
    rr_column_value = (rr_column.strip() if rr_column is not None else DEFAULT_RR_COLUMN)
    service_column_value = _resolve_required_form_value(service_column, DEFAULT_SERVICE_COLUMN, "云服务列名")
    title_column_value = _resolve_required_form_value(title_column, DEFAULT_TITLE_COLUMN, "标题列名")
    if not baseline.filename:
        raise HTTPException(status_code=400, detail=_error_detail(
            code="MISSING_BASELINE_FILE",
            message="未选择基准需求列表。",
            suggestion="请先选择从线上系统或内部主数据导出的基准 Excel 文件。",
        ))
    if not pm_files:
        raise HTTPException(status_code=400, detail=_error_detail(
            code="MISSING_SOURCE_FILE",
            message="未选择来源列表。",
            suggestion="请至少上传一份专项、服务或临时维护的需求列表。",
        ))

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
            raise HTTPException(status_code=400, detail=_error_detail(
                code="NO_VALID_SOURCE_FILE",
                message="没有可分析的来源列表。",
                suggestion="请确认来源列表文件名有效，并重新选择 Excel 文件。",
            ))

        try:
            result = run_v2_workflow(
                baseline_path=baseline_path,
                source_paths=pm_paths,
                output_root=JOBS_DIR,
                config=V2WorkflowConfig(
                    workbook=WorkbookConfig(
                        fe_column=fe_column_value,
                        rr_column=rr_column_value or DEFAULT_RR_COLUMN,
                        service_column=service_column_value,
                        title_column=title_column_value,
                    ),
                    owned_services=tuple(_split_csv(owned_services)),
                    comment_fields=tuple(_split_csv(comment_fields)),
                    comment_template=comment_template or DEFAULT_COMMENT_TEMPLATE,
                    comment_target=comment_target if comment_target in {"fe", "rr", "both"} else "both",
                    sync_linked=sync_linked.lower() in {"true", "1", "yes", "on"},
                    fill_defaults=_parse_fill_defaults(fill_defaults_json),
                ),
            )
        except (BadZipFile, InvalidFileException) as exc:
            raise HTTPException(status_code=400, detail=_error_detail(
                code="INVALID_EXCEL_FILE",
                message="上传文件不是可识别的 Excel 文件。",
                suggestion="请上传 .xlsx 或 .xlsm 文件，不要上传 CSV、临时文件或损坏的 Excel 文件。",
            )) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=_friendly_value_error(str(exc))) from exc

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
        raise HTTPException(status_code=404, detail=_error_detail(
            code="UNKNOWN_OUTPUT_FILE",
            message="下载文件类型不支持。",
            suggestion="请从页面提供的下载入口下载需求汇总包或 sync_plan.json。",
        ))

    path = JOBS_DIR / job_id / "output" / file_name
    if not path.exists():
        raise HTTPException(status_code=404, detail=_error_detail(
            code="OUTPUT_FILE_NOT_FOUND",
            message="下载文件不存在或已被清理。",
            suggestion="请重新执行分析后再下载结果文件。",
        ))

    return FileResponse(path, filename=file_name)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,，]", value) if item.strip()]


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


def _resolve_required_form_value(value: str | None, default: str, label: str) -> str:
    if value is None:
        return default
    if not value.strip():
        raise HTTPException(status_code=400, detail=_error_detail(
            code="FORM_REQUIRED_FIELDS_MISSING",
            message=f"还有必填配置未填写：{label}。",
            suggestion="请补齐页面上带红色星号的必填项后重新开始分析。",
        ))
    return value.strip()


def _error_detail(code: str, message: str, suggestion: str) -> dict[str, str]:
    return {"code": code, "message": message, "suggestion": suggestion}


def _friendly_value_error(message: str) -> dict[str, str]:
    if "baseline missing required columns:" in message:
        missing = message.split(":", 1)[1].strip()
        return _error_detail(
            code="BASELINE_MISSING_REQUIRED_COLUMNS",
            message=f"基准需求列表缺少必填列：{missing}。",
            suggestion="请在基准表中补充这些列后重新上传。基准表至少需要 FE编号、云服务、需求标题。",
        )
    if "Duplicate header in" in message:
        source, columns = _split_duplicate_header_message(message)
        return _error_detail(
            code="DUPLICATE_HEADER",
            message=f"文件 {source} 存在重复表头：{columns}。",
            suggestion="请修改重复列名后重新上传。每个字段在同一个 Excel 中只能出现一次。",
        )
    if "does not contain headers" in message:
        source = message.split(" does not contain headers", 1)[0]
        return _error_detail(
            code="EMPTY_HEADER_ROW",
            message=f"文件 {source} 未识别到表头。",
            suggestion="请确认第 1 行是字段表头，并且至少包含 FE编号、RR编号、云服务或需求标题等字段。",
        )
    if "Invalid fill defaults JSON" in message:
        return _error_detail(
            code="INVALID_FILL_DEFAULTS_JSON",
            message="空值填充规则不是合法 JSON。",
            suggestion='请检查括号、英文双引号和逗号格式。例如：{"云服务":"A"}。',
        )
    if "fill_defaults_json must be an object" in message:
        return _error_detail(
            code="INVALID_FILL_DEFAULTS_TYPE",
            message="空值填充规则必须是 JSON 对象。",
            suggestion='请使用键值对格式，例如：{"云服务":"A"}，不要使用数组或普通文本。',
        )
    return _error_detail(
        code="ANALYSIS_FAILED",
        message="分析失败。",
        suggestion=f"请检查上传文件和页面配置后重试。技术信息：{message}",
    )


def _split_duplicate_header_message(message: str) -> tuple[str, str]:
    payload = message.replace("Duplicate header in", "", 1).strip()
    if ":" not in payload:
        return payload or "未知文件", "未知字段"
    source, columns = payload.split(":", 1)
    return source.strip(), columns.strip()


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
