from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.models import CellValue


DEFAULT_COMMENT_TEMPLATE = """\u3010\u9700\u6c42\u5bf9\u9f50\u7ed3\u8bba\u3011
\u6765\u6e90\u5217\u8868\uff1a{{\u6765\u6e90\u5217\u8868}}
\u4e91\u670d\u52a1\uff1a{{\u4e91\u670d\u52a1}}
\u5173\u8054FE\uff1a{{FE\u7f16\u53f7}}
\u5173\u8054RR\uff1a{{RR\u7f16\u53f7}}
\u5bf9\u9f50\u65f6\u95f4\uff1a{{\u5bf9\u9f50\u65f6\u95f4}}
\u5bf9\u9f50\u5bf9\u8c61\uff1a{{\u5bf9\u9f50\u5bf9\u8c61}}

\u3010\u5bf9\u9f50\u7ed3\u8bba\u3011
{{\u5bf9\u9f50\u7ed3\u8bba}}

\u3010\u8865\u5145\u4fe1\u606f\u3011
{{\u8865\u5145\u4fe1\u606f}}

\u3010\u56de\u5237\u8bf4\u660e\u3011
\u672c\u8bc4\u8bba\u7531\u9700\u6c42\u5217\u8868\u5173\u8054\u5de5\u5177\u6839\u636e\u7528\u6237\u786e\u8ba4\u7ed3\u679c\u751f\u6210\u3002"""


@dataclass
class CommentContext:
    source_name: str
    service: str
    fe_id: str
    rr_id: str
    title: str
    row: dict[str, CellValue]
    selected_fields: list[str]
    extension_fields: list[str] = field(default_factory=list)


@dataclass
class ExtractedCommentVariables:
    aligned_time: str = ""
    aligned_people: str = ""
    values: dict[str, str] = field(default_factory=dict)

