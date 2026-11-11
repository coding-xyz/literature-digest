# 固定流程

目标：**检索/收集固定程序，阅读/提炼/审稿由 AI 完成，最终报告固定程序生成并发布。**  
每次只改内容数据，不改模板和渲染逻辑，保证报告版式一致。

## 角色分工

| 阶段 | 执行者 | 固定产物 |
|---|---|---|
| 检索与收集 | `scripts/collect.py` | `raw/*.json`、`candidates.json`、`manifest.json`、`coverage.json`（构建时） |
| 阅读、筛选、提炼 | AI | `data/<date>/report.json` |
| 全文审稿 | AI | `data/<date>/reviews/<article-id>.json` |
| 合并审稿 | `scripts/merge_reviews.py` | 更新 `report.json` 的 `review` 字段 |
| 报告生成 | `scripts/build_report.py` | `reports/<date>.html`、`coverage.json`、根目录 `index.html` |
| 发布 | `scripts/publish.ps1` | commit + push `index.html` / `reports/` |
| 一致性校验 | `scripts/build_report.py` | 字段、编号、日期、URL、LaTeX、审稿、来源统计 |

## 筛选原则

不得按文件名、arXiv ID 或其他来源前缀筛选。arXiv、ePrint、PRX、PRX Quantum、Nature、Quantum、Science Advances、QST、SciPost 等所有来源同等对待，只看文章内容与主题是否匹配。

非 arXiv 论文用 DOI / 出版社 / accepted manuscript / 作者版获取全文；确实拿不到全文时才写摘要级，并在 `review.basis` 说明。

## 公式契约

AI 生成文本时必须显式标记公式：行内 `\( ... \)`，行间 `$$ ... $$`。不要写裸露的 `^`、`_`、LaTeX 命令或 Unicode 上下标。

`build_report.py` 会检查正文与审稿字段，发现未标记公式直接失败；模板不再做任何自动补渲染。打开折叠的摘要/审稿时，只重新触发 MathJax 排版。

## 自动化任务选择模型

主模型由**目标会话的模型选择**决定，不由任务 prompt 决定。

当前「文献速递」任务绑定到已有会话；`modelSelection.lastUsed` 是 `tgqs-outer / local-glm-5.3-flash`，`pending` 是 `local-deepseek-v4.1-flash`。切换方法：

1. 在 Web GUI 打开该定时任务的目标会话；
2. 用模型选择器切到 `local-deepseek-v4.1-flash`；
3. 下一次新回合/定时投递会应用该选择。

新建任务时，模型由新会话的模型选择或 profile 的 `agent-default-model` 决定；不要指望在 prompt 里写“请用 deepseek”来切换主模型。改默认值会影响所有新会话，配置在：

`C:\Users\Zhou\.dsh\profiles\desktop\cordis.patch.yml`

定时任务的 prompt 是创建/编辑时保存的快照；修改 `AUTOMATION_PROMPT.md` 不会自动更新已存在的任务，需要重新编辑任务 prompt 或重建任务。

## 固定命令

```powershell
$date = "2026-11-11"

# 1. 固定程序：检索 + 收集 + 去重 + 来源状态
python scripts\collect.py --date $date

# 2. AI：读 candidates / 下载全文 / 写 report.json 和 reviews/*.json

# 3. 固定程序：合并审稿 + 校验 + 生成 HTML
python scripts\merge_reviews.py --date $date
python scripts\build_report.py --date $date

# 4. 固定程序：只提交 index.html + reports，并 push
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\publish.ps1 -Date $date
```

一键执行固定部分（AI 已完成 report/reviews 后）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_pipeline.ps1 -Date 2026-11-11 -SkipCollect -Publish
```

`-SkipCollect` 跳过重新抓取；`-Publish` 调用 `publish.ps1`。如果 `report.json` 或 `reviews/` 还没由 AI 生成，脚本会明确停下，不会自行编造内容。

## 自动 push 凭据

`publish.ps1` 只提交 `index.html` 和 `reports/`，不提交 `data/`。

DSH 沙箱中的 Git 凭据可能不可用。给用户环境设置 fine-grained PAT（只勾选该仓库的 **Contents: Read and write**）：

```powershell
[Environment]::SetEnvironmentVariable("GH_TOKEN", "github_pat_xxx", "User")
```

重启 DSH / 终端后再运行。`publish.ps1` 会用 `GH_TOKEN` 通过 HTTPS 推送；没有 token 时回退到 Git Credential Manager。推送失败时任务必须报错，不能回复“已完成”。

## 报告一致性由什么保证

1. **单一模板**：`templates/report-template.html` 是唯一的版式来源。
2. **固定注入点**：`build_report.py` 只替换 `<script id="report-data">`，不改 HTML 结构。
3. **严格校验**：
   - 文章编号必须从 1 连续；
   - 必填字段、URL、日期、重要性、关键词、审稿字段；
   - 至少一篇含 LaTeX；
   - 所有公式必须显式标记，裸露的 `^`、`_`、LaTeX 命令、Unicode 上下标会失败；
   - 收录数与来源统计一致。
4. **来源统计自动计算**：
   - 所有 PR / Nature 子刊逐本展开；
   - 其他来源逐项列出；
   - 汇总折叠在“检索覆盖”下；
   - 抓取 / 去重 / 关键词初筛 / 收录由 `candidates.json` + `manifest.json` 计算。
5. **内容与展示分离**：AI 只写 `report.json` 和 `reviews/*.json`，不直接改 HTML。

## 权限边界

固定流程只读写工作区 `D:\文献调研`：

- 不修改 ACL、注册表、系统目录；
- 不调用 `danger-full-access`；
- 不启动浏览器 / Edge / 无头渲染；
- 不全局安装 Python/npm 包；
- 不写工作区之外路径（临时下载也放在 `data/<date>/pdfs/`）；
- Python 使用工作区运行时或 PATH 中的 `python`；
- `GH_TOKEN` 只作为用户环境变量，不写进仓库。

## 失败处理

- 某个来源失败：`manifest.json` 标记 `error`，报告来源表中保留该来源，不静默当成 0。
- 当天没有新批次：保留最近批次并在 `meta.window` / 报告说明中标注，不写成“今日新增”。
- 全文无法获取：`review` 必须写清只读到摘要，或停止收录该文，不能编造审稿。
- 报告生成失败：不发布旧版 HTML；先修数据，再重跑 `build_report.py`。
- push 失败：任务失败，不回复完成；检查 `GH_TOKEN`、远程分支和冲突。
