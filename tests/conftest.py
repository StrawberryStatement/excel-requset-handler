from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook


FE = "FE\u7f16\u53f7"
RR = "RR\u7f16\u53f7"
TITLE = "\u9700\u6c42\u6807\u9898"
SERVICE = "\u4e91\u670d\u52a1"
STATUS = "\u72b6\u6001"
SCHEDULE = "\u6392\u671f"
OWNER = "\u8d1f\u8d23\u4eba"
PRIORITY = "\u4f18\u5148\u7ea7"
UPDATED_AT = "\u6700\u540e\u66f4\u65b0\u65f6\u95f4"
CONCLUSION = "\u5bf9\u9f50\u7ed3\u8bba"
RISK = "\u4e13\u9879\u98ce\u9669"
CUSTOMER_IMPACT = "\u5ba2\u6237\u5f71\u54cd"
SOURCE_PM = "\u6765\u6e90PM\u6587\u4ef6"


@pytest.fixture
def baseline_headers() -> list[str]:
    return [FE, RR, SERVICE, TITLE, STATUS, SCHEDULE, OWNER, UPDATED_AT]


@pytest.fixture
def baseline_rows() -> list[list[object]]:
    return [
        ["FE-1", "RR-1", "A", "Login polish", "Review", "2026Q2", "Dev A", "2026-05-01"],
        ["FE-2", "RR-2", "B", "Export report", "Doing", "2026Q2", "Dev B", "2026-05-01"],
        ["FE-3", "RR-3", "C", "Approval flow", "Planning", "2026Q3", "Dev C", "2026-05-01"],
    ]


def write_workbook(path: Path, headers: list[str], rows: list[list[object]], sheet_name: str = "requirements") -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def workbook_bytes(headers: list[str], rows: list[list[object]], sheet_name: str = "requirements") -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
