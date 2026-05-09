# 设计说明

## 业务定位

这个系统是一个 Excel 协作层，不替代内部需求系统。

内部需求系统仍然是事实源。Excel 用于产品经理、项目经理、研发同学之间做阶段性对齐。工具负责把多个 PM Excel 收敛成产品经理视角的 FE 总表，并生成待回刷评论清单。

## 主键策略

MVP 只把 `FE编号` 视为唯一 ID。

原因：

- 内部系统可以按 FE 查询和更新。
- 最终回刷对象是研发侧 feature。
- 当前场景里一个 FE 不太会被多个 PM 同时管理。

`RR编号` 不作为唯一 ID，只作为外部需求关联字段保留在总表中。

## 字段分类

### 基准字段

来自基准 Excel 的字段。PM 理论上不能修改。

如果 PM 文件里的基准字段值和基准表不同，系统不会采纳 PM 值，而是写入 `diff_report.xlsx`。

### PM 扩展字段

PM 自己新增的列。系统会：

- 在 `diff_report.xlsx` 的 `extension_columns` sheet 里列出来。
- 在 `quarterly_master.xlsx` 中保留，列名格式为 `来源文件__原列名`。
- 在 `sync_plan.xlsx` 和 `sync_plan.json` 中转换成评论内容。

### 回刷字段

当前 MVP 不直接回刷结构化字段，只生成评论。

未来如果要回刷状态、排期、负责人，可以在 `sync_planner.py` 里新增字段级策略，并在内部系统 API adapter 中实现对应方法。

## 一次分析的输出

每次上传会生成一个 `jobs/{job_id}` 目录：

```text
jobs/{job_id}/
  input/
    baseline.xlsx
    pm_a.xlsx
    pm_b.xlsx
  output/
    quarterly_master.xlsx
    diff_report.xlsx
    sync_plan.xlsx
    sync_plan.json
```

## 内部 API 扩展方式

只建议改这个文件：

```text
backend/app/integrations/internal_system.py
```

建议保持接口简单：

```python
client.get_feature(fe_id)
client.add_comment(fe_id, comment)
```

第一阶段不要直接在上传分析后自动调用 `add_comment`。建议加一个“确认回刷”页面，人工勾选后再调用。

## 后续推荐迭代

1. 增加任务历史列表。
2. 增加页面上的 diff 预览，不只下载 Excel。
3. 增加“人工确认回刷”状态流。
4. 对接内部系统 API，把 `sync_plan` 中确认后的评论写回 FE。
5. 增加字段策略配置，例如哪些 PM 扩展字段进入评论、哪些只保留在总表。
6. 增加 RR 到 FE 的映射异常检测。

