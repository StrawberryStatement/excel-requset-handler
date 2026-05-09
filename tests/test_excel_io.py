from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from backend.app.services.excel_io import load_excel_table, write_table
from tests.conftest import CONCLUSION, FE, RR, TITLE, write_workbook


def test_load_excel_table_preserves_headers_and_ignores_blank_rows(tmp_path: Path) -> None:
    path = tmp_path / "input.xlsx"
    write_workbook(
        path,
        [FE, RR, TITLE, CONCLUSION],
        [
            ["FE-1", "RR-1", "Title 1", "Done"],
            [None, None, None, None],
            ["FE-2", "RR-2", "Title 2", ""],
        ],
    )

    table = load_excel_table(path)

    assert table.headers == [FE, RR, TITLE, CONCLUSION]
    assert len(table.records) == 2
    assert table.records[0][FE] == "FE-1"


def test_write_table_creates_openable_workbook(tmp_path: Path) -> None:
    path = tmp_path / "output.xlsx"

    write_table(path, "master", [FE, TITLE], [{FE: "FE-1", TITLE: "Title 1"}])

    workbook = load_workbook(path)
    sheet = workbook["master"]
    assert sheet["A1"].value == FE
    assert sheet["A2"].value == "FE-1"


def test_load_excel_table_rejects_duplicate_headers(tmp_path: Path) -> None:
    path = tmp_path / "duplicate_headers.xlsx"
    write_workbook(path, [FE, RR, FE], [["FE-1", "RR-1", "FE-1-again"]])

    with pytest.raises(ValueError, match="Duplicate header"):
        load_excel_table(path)
