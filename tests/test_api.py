from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import main
from tests.conftest import CONCLUSION, FE, OWNER, RISK, RR, SCHEDULE, SERVICE, STATUS, TITLE, workbook_bytes


def test_health_endpoint() -> None:
    client = TestClient(main.app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_endpoint_returns_download_urls(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)
    headers = [FE, RR, SERVICE, TITLE, STATUS, SCHEDULE, OWNER]
    baseline_bytes = workbook_bytes(headers, [["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A"]])
    pm_bytes = workbook_bytes(headers + [CONCLUSION], [["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "Aligned"]])

    response = client.post(
        "/api/jobs",
        files=[
            ("baseline", ("baseline.xlsx", baseline_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("pm_alpha.xlsx", pm_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["summary"]["sync_comment_count"] == 2
    assert payload["summary"]["source_list_count"] == 1
    assert payload["preview_rows"][0]["service"] == "A"
    assert payload["downloads"]["package"].endswith("/\u9700\u6c42\u6c47\u603b\u5305.xlsx")

    download = client.get(payload["downloads"]["sync_plan_json"])
    assert download.status_code == 200
    assert any(item[FE] == "FE-1" and item["\u76ee\u6807\u7c7b\u578b"] == "FE" for item in download.json())


def test_download_rejects_unknown_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)

    response = client.get("/api/jobs/not-real/downloads/secrets.txt")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "UNKNOWN_OUTPUT_FILE"


def test_upload_endpoint_returns_400_for_invalid_excel(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)

    response = client.post(
        "/api/jobs",
        files=[
            ("baseline", ("baseline.xlsx", b"not an xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("pm.xlsx", b"not an xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "INVALID_EXCEL_FILE"
    assert "Excel" in detail["message"]


def test_upload_endpoint_sanitizes_windows_invalid_filenames(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)
    headers = [FE, RR, SERVICE, TITLE]
    baseline_bytes = workbook_bytes(headers, [["FE-1", "RR-1", "A", "Login polish"]])
    source_bytes = workbook_bytes(headers + [CONCLUSION], [["FE-1", "RR-1", "A", "Login polish", "Aligned"]])

    response = client.post(
        "/api/jobs",
        files=[
            ("baseline", ("baseline?.xlsx", baseline_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("专项?需求列表.xlsx", source_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 200
    assert response.json()["summary"]["source_list_count"] == 1


def test_upload_endpoint_returns_friendly_missing_baseline_column_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)
    baseline_bytes = workbook_bytes([FE, RR, TITLE], [["FE-1", "RR-1", "Login polish"]])
    source_bytes = workbook_bytes([FE, RR, SERVICE, TITLE], [["FE-1", "RR-1", "A", "Login polish"]])

    response = client.post(
        "/api/jobs",
        files=[
            ("baseline", ("baseline.xlsx", baseline_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("source.xlsx", source_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "BASELINE_MISSING_REQUIRED_COLUMNS"
    assert "基准需求列表缺少必填列" in detail["message"]
    assert "重新上传" in detail["suggestion"]


def test_upload_endpoint_returns_friendly_duplicate_header_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)
    baseline_bytes = workbook_bytes([FE, RR, SERVICE, TITLE, FE], [["FE-1", "RR-1", "A", "Login polish", "FE-1"]])
    source_bytes = workbook_bytes([FE, RR, SERVICE, TITLE], [["FE-1", "RR-1", "A", "Login polish"]])

    response = client.post(
        "/api/jobs",
        files=[
            ("baseline", ("baseline.xlsx", baseline_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("source.xlsx", source_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "DUPLICATE_HEADER"
    assert "重复表头" in detail["message"]


def test_upload_endpoint_rejects_blank_required_form_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)
    headers = [FE, RR, SERVICE, TITLE]
    baseline_bytes = workbook_bytes(headers, [["FE-1", "RR-1", "A", "Login polish"]])
    source_bytes = workbook_bytes(headers, [["FE-1", "RR-1", "A", "Login polish"]])

    response = client.post(
        "/api/jobs",
        data={"service_column": " "},
        files=[
            ("baseline", ("baseline.xlsx", baseline_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("source.xlsx", source_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "FORM_REQUIRED_FIELDS_MISSING"
    assert "云服务列名" in detail["message"]


def test_upload_endpoint_splits_comment_fields_by_chinese_comma(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "JOBS_DIR", tmp_path / "jobs")
    client = TestClient(main.app)
    headers = [FE, RR, SERVICE, TITLE]
    baseline_bytes = workbook_bytes(headers, [["FE-1", "RR-1", "A", "Login polish"]])
    source_bytes = workbook_bytes(
        headers + [CONCLUSION, RISK],
        [["FE-1", "RR-1", "A", "Login polish", "Aligned", "Low risk"]],
    )

    response = client.post(
        "/api/jobs",
        data={"comment_fields": f"{CONCLUSION}，{RISK}"},
        files=[
            ("baseline", ("baseline.xlsx", baseline_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("pm_files", ("source.xlsx", source_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )

    assert response.status_code == 200
    row = response.json()["preview_rows"][0]
    assert CONCLUSION in row["extension_summary"]
    assert RISK in row["extension_summary"]
