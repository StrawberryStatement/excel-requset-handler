# 需求列表关联工作台

这是一个面向产品经理的 Excel 需求列表关联与梳理 MVP。它的目标不是做普通表格 diff，而是把多份不同来源的需求列表按 `FE编号`、`RR编号`、`云服务` 关联起来，形成统一的需求汇总包，并生成待人工确认的回刷评论清单。

## 适用场景

- 你同时负责多个云服务，例如 A、B 服务。
- 你也负责多个专项，专项里可能包含 A、B、C、D 多个云服务。
- 项目经理、专项负责人或其他协作方会各自维护不同形态的需求列表。
- 你需要把这些列表汇总成产品经理视角的统一需求列表。
- 对齐后的结论需要以评论形式回刷到内部需求管理系统。

## 当前 MVP 能力

- 上传一份基准需求列表和多份来源需求列表。
- 基于 `FE编号`、`RR编号`、`云服务` 做关联分析。
- 输出 FE 视角、RR 视角、专项/来源列表视角和我负责的云服务视角。
- 识别常见异常：
  - 缺少 `云服务` 列或云服务为空
  - 缺少 FE/RR 主键
  - RR 有但 FE 为空，标记为待建 FE
  - FE 有但 RR 为空，标记为无外部 RR
  - 同一个 FE 被多个来源共同管理
  - FE 和云服务归属冲突
- 保留来源列表中的扩展字段，并在页面和导出包中并排展示。
- 生成待回刷评论清单，支持 FE、RR、FE+RR 三类目标。
- 评论模板支持在浏览器本地保存、编辑、删除。
- 内部系统 API 只预留接口，不直接调用真实系统。

## 一键启动

推荐直接双击：

```text
start.bat
```

或者在 PowerShell 中执行：

```powershell
.\start.ps1
```

脚本会自动完成：

1. 创建 `.venv` 虚拟环境。
2. 安装 `requirements.txt` 依赖。
3. 重新生成 `samples` 目录下的示例 Excel。
4. 启动 FastAPI 服务。
5. 打开浏览器访问 `http://127.0.0.1:8000/`。

## 手动启动

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe samples\make_sample_workbook.py
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000/
```

## 示例文件

启动脚本会生成以下示例文件：

```text
samples\baseline.xlsx
samples\pm_a.xlsx
samples\pm_b.xlsx
samples\基准需求列表.xlsx
samples\专项1需求列表.xlsx
samples\服务A需求列表.xlsx
```

页面上传时：

- 基准 Excel：选择 `samples\baseline.xlsx` 或 `samples\基准需求列表.xlsx`
- 来源列表：选择 `samples\pm_a.xlsx`、`samples\pm_b.xlsx`，或对应中文文件名

## 推荐表头

基准需求列表建议至少包含：

```text
FE编号
RR编号
云服务
需求标题
状态
排期
负责人
```

来源需求列表可以在这些列之外新增任意扩展列，例如：

```text
专项风险
对齐结论
会议时间
客户影响
会议纪要
```

如果来源列表缺少 `云服务`，系统会认为这是数据问题。页面支持配置空值填充规则，但原始数据仍会保留在导出包中，避免静默修改来源表。

## 输出结果

分析完成后，页面会展示在线预览，并提供一个统一下载：

```text
需求汇总包.xlsx
```

汇总包包含：

- 总览
- FE视角需求清单
- RR视角需求清单
- 专项视角需求清单
- 我负责的云服务需求
- 来源列表扩展字段
- 待回刷评论
- 待建FE
- 异常项
- 原始行数据

同时后端会生成：

```text
sync_plan.json
```

这个 JSON 用于后续接入内部需求管理系统 API。

## 内部系统 API 预留位置

后续在内网环境中重点改这里：

```text
backend/app/integrations/internal_system.py
```

当前已经预留：

```python
get_feature(fe_id: str) -> dict
add_comment(fe_id: str, comment: str) -> dict
get_requirement(rr_id: str) -> dict
add_requirement_comment(rr_id: str, comment: str) -> dict
```

MVP 默认不直接调用内部系统，只生成待人工确认的回刷清单。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

当前覆盖：

- Excel 读取与导出
- 基准列差异识别
- 多来源扩展字段合并
- 待回刷评论生成
- V2 FE/RR/云服务关联工作流
- API 上传与下载
- Windows 文件名清洗

## 目录结构

```text
backend/
  app/
    main.py                         # FastAPI API 和静态页面入口
    models.py                       # 数据模型和默认字段配置
    commenting/                     # 评论模板、变量抽取、模型抽取预留
    services/
      v2_workflow.py                # 当前主工作流
      excel_io.py                   # Excel 读取与导出
      diff_engine.py                # 旧版 diff 引擎，保留测试覆盖
      merge_engine.py               # 旧版合并引擎，保留测试覆盖
      sync_planner.py               # 旧版回刷清单生成，保留测试覆盖
    integrations/
      internal_system.py            # 内部系统 API 适配器预留
frontend/
  index.html
  app.js
  styles.css
samples/
  make_sample_workbook.py
tests/
docs/
```

