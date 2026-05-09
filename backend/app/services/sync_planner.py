from __future__ import annotations

from collections import defaultdict

from backend.app.models import ExcelTable, PmAnalysis, SyncComment, WorkbookConfig
from backend.app.services.excel_io import normalize_cell


def build_sync_comments(
    baseline: ExcelTable,
    analyses: list[PmAnalysis],
    config: WorkbookConfig,
) -> list[SyncComment]:
    baseline_by_fe = baseline.by_key(config.fe_column)
    comments_by_fe: dict[str, list[str]] = defaultdict(list)
    sources_by_fe: dict[str, list[str]] = defaultdict(list)

    for analysis in analyses:
        for pm_row in analysis.pm_table.records:
            fe_id = normalize_cell(pm_row.get(config.fe_column))
            if not fe_id:
                continue

            lines: list[str] = []
            for column in analysis.extension_columns:
                value = normalize_cell(pm_row.get(column))
                if value:
                    lines.append(f"{column}: {value}")

            if lines:
                comments_by_fe[fe_id].append(f"[{analysis.source_name}]\n" + "\n".join(lines))
                if analysis.source_name not in sources_by_fe[fe_id]:
                    sources_by_fe[fe_id].append(analysis.source_name)

    sync_comments: list[SyncComment] = []
    for fe_id, blocks in comments_by_fe.items():
        baseline_row = baseline_by_fe.get(fe_id, {})
        title = normalize_cell(baseline_row.get(config.title_column))
        sync_comments.append(SyncComment(
            fe_id=fe_id,
            title=title,
            comment="\n\n".join(blocks),
            source_names=sources_by_fe[fe_id],
        ))

    return sync_comments

