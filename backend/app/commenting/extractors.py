from __future__ import annotations

import re

from backend.app.commenting.schemas import CommentContext, ExtractedCommentVariables
from backend.app.services.excel_io import normalize_cell


TIME_FIELD_HINTS = (
    "\u5bf9\u9f50\u65f6\u95f4",
    "\u4f1a\u8bae\u65f6\u95f4",
    "\u6c9f\u901a\u65f6\u95f4",
    "\u65f6\u95f4",
)
PEOPLE_FIELD_HINTS = (
    "\u5bf9\u9f50\u5bf9\u8c61",
    "\u53c2\u4e0e\u4eba",
    "\u6c9f\u901a\u5bf9\u8c61",
    "\u4f1a\u8bae\u5bf9\u8c61",
)


def extract_comment_variables(context: CommentContext) -> ExtractedCommentVariables:
    variables = ExtractedCommentVariables()
    variables.aligned_time = _extract_by_field_name(context.row, TIME_FIELD_HINTS)
    variables.aligned_people = _extract_by_field_name(context.row, PEOPLE_FIELD_HINTS)

    joined_text = "\n".join(
        normalize_cell(context.row.get(field))
        for field in context.selected_fields
        if normalize_cell(context.row.get(field))
    )

    if not variables.aligned_time:
        variables.aligned_time = _extract_time_from_text(joined_text)
    if not variables.aligned_people:
        variables.aligned_people = _extract_people_from_text(joined_text)

    return variables


def _extract_by_field_name(row: dict, hints: tuple[str, ...]) -> str:
    for field, value in row.items():
        if any(hint in str(field) for hint in hints):
            normalized = normalize_cell(value)
            if normalized:
                return normalized
    return ""


def _extract_time_from_text(text: str) -> str:
    patterns = [
        r"(20\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2})",
        r"(\d{1,2}\u6708\d{1,2}\u65e5)",
        r"(\d{1,2}/\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def _extract_people_from_text(text: str) -> str:
    patterns = [
        r"\u548c([^,\uff0c\u3002\n]{1,20})\u5bf9\u9f50",
        r"\u4e0e([^,\uff0c\u3002\n]{1,20})\u786e\u8ba4",
        r"([^,\uff0c\u3002\n]{1,20})\u4f1a\u8bae",
        r"([^,\uff0c\u3002\n]{1,20})\u8bc4\u5ba1",
        r"([^,\uff0c\u3002\n]{1,20})\u6c9f\u901a",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""

