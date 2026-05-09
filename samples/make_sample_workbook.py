from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


SAMPLE_DIR = Path(__file__).resolve().parent

FE = "FE\u7f16\u53f7"
RR = "RR\u7f16\u53f7"
SERVICE = "\u4e91\u670d\u52a1"
TITLE = "\u9700\u6c42\u6807\u9898"
STATUS = "\u72b6\u6001"
SCHEDULE = "\u6392\u671f"
OWNER = "\u8d1f\u8d23\u4eba"


def write_workbook(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "requirements"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def main() -> None:
    headers = [FE, RR, SERVICE, TITLE, STATUS, SCHEDULE, OWNER]
    baseline_rows = [
        ["FE-1001", "RR-001", "A", "\u767b\u5f55\u4f53\u9a8c\u4f18\u5316", "\u5f85\u8bc4\u5ba1", "2026Q2", "\u7814\u53d1A"],
        ["FE-1002", "RR-002", "B", "\u62a5\u8868\u5bfc\u51fa\u80fd\u529b", "\u5f00\u53d1\u4e2d", "2026Q2", "\u7814\u53d1B"],
        ["FE-1003", "RR-003", "C", "\u5ba1\u6279\u94fe\u8def\u8c03\u6574", "\u5f85\u6392\u671f", "2026Q3", "\u7814\u53d1C"],
        ["FE-1004", "", "A", "\u5185\u90e8\u89c4\u5212\u80fd\u529b", "\u89c4\u5212\u4e2d", "2026Q3", "\u7814\u53d1D"],
    ]

    list_a_headers = headers + ["\u4e13\u9879\u98ce\u9669", "\u5bf9\u9f50\u7ed3\u8bba", "\u4f1a\u8bae\u65f6\u95f4"]
    list_a_rows = [
        ["FE-1001", "RR-001", "A", "\u767b\u5f55\u4f53\u9a8c\u4f18\u5316", "\u5f85\u8bc4\u5ba1", "2026Q2", "\u7814\u53d1A", "\u4f9d\u8d56\u7f51\u5173\u6539\u9020", "\u548c\u7814\u53d1A\u5bf9\u9f50\uff0c\u5148\u505a\u7070\u5ea6", "2026-05-09"],
        ["", "RR-009", "B", "\u5ba2\u6237\u65b0\u589e\u9700\u6c42", "\u5f85\u62c6\u5206", "2026Q3", "", "\u9700\u8981\u65b0\u5efaFE", "\u4e0e\u9879\u76ee\u7ecf\u7406\u786e\u8ba4\u9700\u8981\u62c6FE", ""],
    ]

    list_b_headers = headers + ["\u5ba2\u6237\u5f71\u54cd", "\u4f1a\u8bae\u7eaa\u8981"]
    list_b_rows = [
        ["FE-1003", "RR-003", "C", "\u5ba1\u6279\u94fe\u8def\u8c03\u6574", "\u5f85\u6392\u671f", "2026Q3", "\u7814\u53d1C", "\u5f71\u54cd\u4e09\u4e2a\u8bd5\u70b9\u5ba2\u6237", "\u9700\u8981\u8865\u5145\u56de\u6eda\u65b9\u6848"],
        ["FE-1004", "", "A", "\u5185\u90e8\u89c4\u5212\u80fd\u529b", "\u89c4\u5212\u4e2d", "2026Q3", "\u7814\u53d1D", "", "\u5185\u90e8\u4f1a\u8bae\u786e\u8ba4\u4e0d\u9700\u8981RR"],
    ]

    write_workbook(SAMPLE_DIR / "baseline.xlsx", headers, baseline_rows)
    write_workbook(SAMPLE_DIR / "pm_a.xlsx", list_a_headers, list_a_rows)
    write_workbook(SAMPLE_DIR / "pm_b.xlsx", list_b_headers, list_b_rows)
    write_workbook(SAMPLE_DIR / "\u57fa\u51c6\u9700\u6c42\u5217\u8868.xlsx", headers, baseline_rows)
    write_workbook(SAMPLE_DIR / "\u4e13\u98791\u9700\u6c42\u5217\u8868.xlsx", list_a_headers, list_a_rows)
    write_workbook(SAMPLE_DIR / "\u670d\u52a1A\u9700\u6c42\u5217\u8868.xlsx", list_b_headers, list_b_rows)


if __name__ == "__main__":
    main()
