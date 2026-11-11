# 固定流程

目标：**检索/收集固定程序，阅读/提炼/审稿由 AI 完成，最终报告固定程序生成并发布。**

## 角色分工

| 阶段 | 执行者 | 固定产物 |
|---|---|---|
| 检索与收集 | `scripts/collect.py` | `raw/*.json`、`candidates.json`、`manifest.json` |
| 动态篇数预算 | `scripts/selection_budget.py` | `selection_budget.json` |
| 阅读、筛选、提炼 | AI | `data/<date>/report.json` |
| 全文审稿 | AI | `data/<date>/reviews/<article-id>.json` |
| 合并审稿 | `scripts/merge_reviews.py` | 更新 `report.json` 的 `review` 字段 |
| 报告生成 | `scripts/build_report.py` | `reports/<date>.html`、`coverage.json`、根目录 `index.html` |
| 发布 | `scripts/publish.ps1` | commit + push `index.html` / `reports/` |
| 一致性校验 | `scripts/build_report.py` | 字段、编号、日期、URL、LaTeX、审稿、来源统计 |

## 筛选原则

不按文件名、arXiv ID 或其他来源前缀筛选。arXiv、ePrint、PRX、PRX Quantum、Nature、Quantum、Science Advances、QST、SciPost 等所有来源同等对待，只看文章内容与主题是否匹配。

非 arXiv 论文用 DOI / 出版社 / accepted manuscript / 作者版获取全文；确实拿不到全文时才写摘要级，并在 `review.basis` 说明。

## 公式契约

AI 生成文本时必须显式标记公式：行内 `\( ... \)`，行间 `$$ ... $$`。不要写裸露的 `^`、`_`、LaTeX 命令或 Unicode 上下标。

`build_report.py` 会检查正文与审稿字段，发现未标记公式直接失败；模板不做任何自动补渲染。打开折叠的摘要/审稿时，只重新触发 MathJax 排版。

## 动态篇数

`selection_budget.py` 读取历史 `report.json` 中重要性 5 的文章，提取主题，与当天候选池比较，输出 `target_articles` / `target_must_read` / `quality_ratio`。

这是建议值，不是硬配额。AI 可以按候选池质量调整，但不能把旧文凑数。

## 固定命令

```powershell
$date = "<date>"

# 1. 检索 + 收集 + 去重 + 来源状态
python scripts\collect.py --date $date

# 2. 动态篇数建议
python scripts\selection_budget.py --date $date

# 3. AI：读 candidates / 下载全文 / 写 report.json 和 reviews/*.json

# 4. 合并 + 校验 + 生成
python scripts\merge_reviews.py --date $date
python scripts\build_report.py --date $date

# 5. 只提交 index.html + reports，并 push
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\publish.ps1 -Date $date
```

固定部分一键执行（AI 已完成 report/reviews 后）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_pipeline.ps1 -Date <date> -SkipCollect -Publish
```

## SCOPE.md 编辑

`SCOPE.md` 的 `SCOPE_CONFIG` JSON 块是运行配置来源。修改后，`collect.py` 会自动同步到 `config/scope.json`。

控制项包括：arXiv 分类、关键词、Nature feeds、PR journals、其他期刊、Quantum/ePrint feed、回看天数。

## 报告一致性

1. 单一模板：`templates/report-template.html` 是唯一版式来源。
2. 固定注入点：`build_report.py` 只替换 `<script id="report-data">`。
3. 严格校验：
   - 文章编号从 1 连续；
   - 必填字段、URL、日期、重要性、关键词、审稿字段；
   - 至少一篇含 LaTeX；
   - 公式必须显式标记；
   - 收录数与来源统计一致。
4. 来源统计自动计算：PR/Nature 子刊逐本展开，其他来源逐项列出，汇总折叠在“检索覆盖”下。
5. 内容与展示分离：AI 只写 `report.json` 和 `reviews/*.json`，不直接改 HTML。

## 模型选择

主模型由**目标会话的模型选择**决定，不由任务 prompt 决定。给定时任务换模型时：

1. 打开该任务绑定的目标会话；
2. 用会话模型选择器切换；
3. 下一次新回合/定时投递应用该模型。

新建任务时，模型由新会话选择或 profile 的 `agent-default-model` 决定。修改 `AUTOMATION_PROMPT.md` 不会自动更新已存在的定时任务。

## 自动 push

`publish.ps1` 只提交 `index.html` 和 `reports/`，不提交 `data/`。

设置仓库级 fine-grained PAT（**Contents: Read and write**）到用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable("GH_TOKEN", "github_pat_xxx", "User")
```

`publish.ps1` 会读取用户环境变量，用 OpenSSL + token 推送。推送失败时任务失败，不回复“已完成”。

## 权限边界

- 不修改 ACL、注册表、系统目录；
- 不调用 `danger-full-access`；
- 不启动浏览器 / Edge / 无头渲染；
- 不全局安装 Python/npm 包；
- 不写工作区之外路径；
- `GH_TOKEN` 只作为用户环境变量，不写进仓库。

## 失败处理

- 来源失败：`manifest.json` 标记 `error`，报告保留该来源，不静默当成 0。
- 当天没有新批次：保留最近批次并标注，不写成“今日新增”。
- 全文无法获取：`review` 写清只读到摘要，或停止收录；不能编造。
- 报告生成失败：不发布旧版 HTML。
- push 失败：任务失败；检查 `GH_TOKEN`、远程分支和冲突。
