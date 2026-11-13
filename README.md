# 文献速递

一个本地可运行的文献监测、阅读与发布工作流。

- **程序负责**：检索、收集、去重、来源统计、校验、生成 HTML、发布静态页面。
- **AI 负责**：阅读全文、筛选、提炼、写批判性审稿、总结。
- **模板负责**：统一报告结构，保证每次输出形式一致。

当前主题：**容错量子计算与超导量子计算机仿真**。

## 文件

| 路径 | 用途 |
|---|---|
| [`index.html`](index.html) | 汇总页：日历、日/周切换、嵌入每日报告 |
| [`reports/`](reports/) | 每日生成的自包含 HTML 报告 |
| [`templates/report-template.html`](templates/report-template.html) | 报告模板 |
| [`templates/index-template.html`](templates/index-template.html) | 汇总页模板 |
| [`SCOPE.md`](SCOPE.md) | 检索范围；含机器可读的 `SCOPE_CONFIG` |
| [`config/scope.json`](config/scope.json) | 由 `SCOPE_CONFIG` 同步出的运行配置 |
| [`scripts/collect.py`](scripts/collect.py) | 检索、收集、去重、来源统计 |
| [`scripts/selection_budget.py`](scripts/selection_budget.py) | 根据历史必读文章与当天候选池计算动态篇数预算 |
| [`scripts/assemble_report.py`](scripts/assemble_report.py) | 从每篇小 JSON 组装 report.json |
| [`scripts/merge_reviews.py`](scripts/merge_reviews.py) | 合并 AI 审稿 |
| [`scripts/build_report.py`](scripts/build_report.py) | 校验并生成报告与汇总页 |
| [`scripts/publish.ps1`](scripts/publish.ps1) | 只提交 `index.html` 与 `reports/` 并 push |
| [`scripts/run_pipeline.ps1`](scripts/run_pipeline.ps1) | 固定步骤的一键入口 |
| [`PIPELINE.md`](PIPELINE.md) | 完整流程与约束 |
| [`AUTOMATION_PROMPT.md`](AUTOMATION_PROMPT.md) | 每日自动化任务 Prompt |

`data/` 是构建期数据，已加入 `.gitignore`，不发布到 GitHub。网页本身不依赖它。

## 报告长什么样

- 大标题：**文献速递**
- 小标题：**容错量子计算与超导量子计算机仿真**
- 顶部搜索框已移除；用关键词筛选。
- 每篇包含：问题 / 方法 / 结果 / 关键贡献 / 局限。
- 重要性 1–5，是阅读优先级，不是论文质量评级。
- 重要数学结果直接用 LaTeX 写在正文，由本地 MathJax 渲染。
- “摘要原文”和“AI 审稿”默认折叠；AI 审稿单栏、分点列表。
- 右侧悬浮“目录”可跳到任意文章；手机端可隐藏。
- 来源统计折叠在“检索覆盖”下：预印本、PR/Nature 各子刊、其他期刊逐项列出。
- 页面支持打印和本地笔记；笔记只存在浏览器。

## 固定流程

```text
collect.py
  ↓
selection_budget.py（动态篇数建议）
  ↓
AI 阅读全文 / 写 meta.json + articles/*.json + reviews/*.json
  ↓
assemble_report.py（拼成 report.json）
  ↓
merge_reviews.py
  ↓
build_report.py（校验 + 生成 reports/<date>.html + index.html）
  ↓
publish.ps1（commit + push）
  ↓
GitHub Pages 自动部署
```

一键执行固定部分（AI 已写完 report/reviews 后）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_pipeline.ps1 -Date <date> -SkipCollect -Publish
```

## SCOPE.md 是编辑入口

`SCOPE.md` 中有一个 `SCOPE_CONFIG` JSON 块，控制：

- arXiv 分类
- 核心 / 排除关键词
- Nature 各刊 RSS
- PR 各刊 ISSN
- 其他 OA/混合期刊
- Quantum / ePrint feed
- 回看天数

修改该块后，运行 `collect.py` 会自动同步到 `config/scope.json` 并生效。  
`SCOPE.md` 的 prose 是说明；代码以 `SCOPE_CONFIG` 为准。

## 长 JSON 写入保护

不要一次写超长的 `report.json`。AI 按篇写 `data/<date>/articles/01.json`、`02.json`……，再运行：

```powershell
python scripts\assemble_report.py --date <date>
```

所有生成脚本使用临时文件 + `os.replace` 原子写入，进程中断不会留下半截 HTML/JSON。

## 动态篇数

`selection_budget.py` 读取历史 `report.json` 中重要性 5 的文章，提取主题，与当天候选池比较，输出：

```text
data/<date>/selection_budget.json
  target_articles
  target_must_read
  quality_ratio
  ...
```

这是建议值，不是死配额；候选池特别强或特别弱时可以人工调整。

## 发布到 GitHub Pages

```powershell
git push origin main
```

Pages 的 `Deploy static site to GitHub Pages` workflow 只发布：

```text
index.html
reports/
assets/
SCOPE.md
.nojekyll
```

### 自动 push 凭据

`publish.ps1` 只提交 `index.html` 和 `reports/`，不提交 `data/`。  
设置仓库级 fine-grained PAT（**Contents: Read and write**）到用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable("GH_TOKEN", "github_pat_xxx", "User")
```

不要在仓库或聊天中保存 token。`publish.ps1` 会自动读取用户环境变量，并用 OpenSSL + token 推送；失败时任务必须报错，不能假装完成。

## 边界

- 不按文件名或来源前缀筛选；只看内容与主题。
- 不把旧文写成今日新增。
- 不把摘要写成全文精读。
- 不把旧版 HTML 当新报告发布。
- 不自动修改 ACL、系统设置或全局依赖。
