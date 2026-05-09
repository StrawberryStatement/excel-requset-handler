from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import main
from tests.conftest import CONCLUSION, FE, OWNER, RR, SCHEDULE, SERVICE, STATUS, TITLE, workbook_bytes


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
