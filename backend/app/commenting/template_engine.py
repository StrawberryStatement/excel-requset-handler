from __future__ import annotations

from backend.app.commenting.extractors import extract_comment_variables
from backend.app.commenting.schemas import CommentContext, DEFAULT_COMMENT_TEMPLATE
from backend.app.services.excel_io import normalize_cell


def render_comment(context: CommentContext, template: str | None = None) -> str:
    template = template or DEFAULT_COMMENT_TEMPLATE
    extracted = extract_comment_variables(context)
    conclusion = _first_non_empty(context.row, ["\u5bf9\u9f50\u7ed3\u8bba", "\u7ed3\u8bba"])
    supplemental = _build_supplemental(context)

    values = {
        "\u6765\u6e90\u5217\u8868": context.source_name,
        "\u4e91\u670d\u52a1": context.service,
        "FE\u7f16\u53f7": context.fe_id,
        "RR\u7f16\u53f7": context.rr_id,
        "\u9700\u6c42\u6807\u9898": context.title,
        "\u5bf9\u9f50\u65f6\u95f4": extracted.aligned_time,
        "\u5bf9\u9f50\u5bf9\u8c61": extracted.aligned_people,
        "\u5bf9\u9f50\u7ed3\u8bba": conclusion,
        "\u8865\u5145\u4fe1\u606f": supplemental,
    }

    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return _drop_empty_variable_lines(rendered)


def _first_non_empty(row: dict, candidates: list[str]) -> str:
    for candidate in candidates:
        value = normalize_cell(row.get(candidate))
        if value:
            return value
    return ""


def _build_supplemental(context: CommentContext) -> str:
    lines: list[str] = []
    skipped = {"\u5bf9\u9f50\u7ed3\u8bba", "\u7ed3\u8bba"}
    for field in context.selected_fields:
        if field in skipped:
            continue
        value = normalize_cell(context.row.get(field))
        if value:
            lines.append(f"{field}\uff1a{value}")
    return "\n".join(lines)


def _drop_empty_variable_lines(text: str) -> str:
    lines: list[str] = []
    previous_blank = False
    for line in text.splitlines():
        stripped = line.strip()
        has_unresolved_variable = "{{" in line and "}}" in line
        ends_with_empty_label = stripped.endswith("\uff1a")
        if has_unresolved_variable or ends_with_empty_label:
            continue
        if not stripped:
            if previous_blank:
                continue
            previous_blank = True
            lines.append("")
            continue
        previous_blank = False
        lines.append(line)
    return "\n".join(lines).strip()

