# 文献速递：容错量子计算与超导量子计算机仿真

一个偏“读论文”的本地工作流：把最近论文收进同一张清单，每篇按 **问题 / 方法 / 结果 / 关键贡献 / 局限** 拆解；重要的数学结果必须用显式 LaTeX 标记，由 build_report.py 校验、MathJax 渲染；不在渲染阶段自动补公式。

当前示例：**2026-11-09**，13 篇，8 个关键公式，5 篇“必读”。抓取 844 篇、去重 842 篇、关键词初筛 113 篇、收录 13 篇；arXiv 11、PRX 1、PRX Quantum 1。截至 22:30，arXiv 周一公告尚未发布，用的是 11-03—11-06 最近批次，不写成“今日新增”。

## 文件

| 文件 | 用途 |
|---|---|
| [`SCOPE.md`](SCOPE.md) | 两个核心方向、关键词、边界/排除、检索网址 |
| [`templates/report-template.html`](templates/report-template.html) | 文章列表模板，含演示数据与 MathJax |
| [`index.html`](index.html) | 汇总页：右上角日历、日/周切换、嵌入每日报告 |\n| [`reports/2026-11-09.html`](reports/2026-11-09.html) | 本次 13 篇的完整报告 |
| `data/2026-11-09/report.json` | 人工提炼后的报告数据（仅本地，不同步 GitHub） |
| `data/2026-11-09/reviews/` | 13 份全文 AI 审稿 JSON（仅本地） |
| `data/2026-11-09/pdfs/` | 13 篇全文 PDF 与抽取文本（仅本地） |
| [`assets/mathjax/tex-svg.js`](assets/mathjax/tex-svg.js) | 本地 MathJax，离线渲染公式 |
| `data/2026-11-09/manifest.json` | 抓取快照与来源状态（仅本地） |

## 页面长什么样

- 大标题：**文献速递**；小标题：**容错量子计算与超导量子计算机仿真**。
- 没有搜索框、没有趋势判断、没有大型来源仪表盘；只显示来源统计：
  `arXiv 11 · PRX 1 · PRX Quantum 1`。
- 顶部是一排关键词：编译与验证、解码器、大规模仿真、纠错码、芯片与耦合器、容错实验、测控与噪声、Pauli 传播、经典模拟、边界。
- 每篇固定：
  - 标题 / 中文标题 / 作者 / 来源 / 日期；
  - **结论**；
  - **问题 / 方法 / 结果 / 关键贡献 / 局限**；
  - 正文中的 LaTeX 公式直接由 MathJax 渲染；
  - 关键数字、原文 / PDF / DOI；
  - 阅读状态与本地笔记。
- 左侧不是分类字母，而是 **1–5 的重要性参考**（5=必读，4=高，3=中，2=参考）。这是阅读优先级，不是论文质量评级。
- 颜色：蓝、橙、绿、紫、琥珀等高对比度小面积色块，正文仍是深灰黑，避免整页灰。

## 公式

公式直接写在 `summary`、`problem`、`method`、`result`、`contribution` 等文本字段里，用：

- 行内：`\\( ... \\)`
- 行间：`$$ ... $$`

页面用本地 `assets/mathjax/tex-svg.js` 渲染成 SVG，不依赖 CDN。没有单独的“关键公式”框，公式出现在它该出现的论证位置。

## AI 审稿

每篇“摘要原文”下面有一个默认折叠的 **AI 审稿 · 批判性阅读**，包含：

- 审稿结论（拒稿 / 弱拒 / 大修 / 小修 / 接受）与置信度；
- 核心主张是否成立；
- 主要缺陷（基线、假设、验证范围）；
- 是否夸大；
- 需要核对的引用 / 实验；
- 要作者回答的问题；
- 审稿依据（读了全文哪些部分、是否只读到摘要）。

审稿基于 PDF 全文、关键公式/定理、结果表和结论，必要处指出应核对的引用；它是 AI 生成的批判性阅读，不是同行评审。

## 汇总页

打开根目录 [index.html](index.html)：

- 主体是每日报告的 iframe，原样展示 `reports/*.html`。
- 右上角日历选择日期；橙色点表示当天有报告。
- 切到“周”模式后，按 ISO 周列出报告；选择一周显示周视图，可下钻到任意一天。
- `build_report.py` 每次生成报告后会调用 `build_index.py`，自动扫描 `reports/` 并重建汇总页；新增/删除报告后也可单独运行 `python scripts\build_index.py`。

## 固定流程与自动化

- 检索 / 收集：`scripts/collect.py`，固定输出 raw、candidates、manifest。
- 阅读 / 提炼 / 审稿：由 AI 写 `data/<date>/report.json` 与 `data/<date>/reviews/*.json`；不按文件名/arXiv ID 前缀筛选，所有来源同等对待。
- 合并 / 校验 / 生成：`scripts/merge_reviews.py` + `scripts/build_report.py`，固定模板与字段校验；来源统计由 `candidates.json` + `manifest.json` 自动计算，PR/Nature 子刊逐本展开，折叠在“期刊”下。
- 一键执行固定程序：`scripts/run_pipeline.ps1 -Date 2026-11-09`。
- 完整流程说明：[PIPELINE.md](PIPELINE.md)
- 每日任务 prompt：[AUTOMATION_PROMPT.md](AUTOMATION_PROMPT.md)

## 运行

```powershell
# 1. 抓取最近 7 天候选（arXiv / ePrint / PR / Nature / Quantum / Science Advances / SciPost / AVS / QST）
python scripts\collect.py --date 2026-11-09

# 2. 人工筛选后编辑 data\2026-11-09\report.json

# 3. 校验并生成
python scripts\build_report.py --date 2026-11-09
```

Windows 下如果 `python` 不在 PATH：

```powershell
C:\Users\Zhou\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe scripts\collect.py --date 2026-11-09
C:\Users\Zhou\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe scripts\build_report.py --date 2026-11-09
```

自动抓取覆盖 arXiv、ePrint、PR 系列、Nature 系列、Quantum、Science Advances、SciPost Physics、AVS Quantum Science、Quantum Science and Technology；Crossref 用于 PR 系列和四本无稳定 RSS 的 OA/混合期刊。

## 发布到 GitHub Pages

`data/` 是构建期数据，已经写进 `.gitignore`；网页本身不需要它。用户打开页面看到的是静态的 `index.html`、`reports/*.html` 和 `assets/mathjax/`，所以不提交 `data/` 不影响阅读。

发布步骤：

```powershell
cd D:\文献调研
git init
git add .
git commit -m "publish literature digest"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

然后到 GitHub 仓库：

1. **Settings → Pages**
2. **Build and deployment → Source** 选择 **GitHub Actions**
3. 推送后 `.github/workflows/pages.yml` 会自动把 `index.html`、`reports/`、`assets/`、`SCOPE.md` 和 `.nojekyll` 发布到 Pages
4. 页面地址通常是：

```text
https://<你的用户名>.github.io/<仓库名>/
```

### 以后新增一期报告

```powershell
python scripts\build_report.py --date 2026-11-11
git add reports\2026-11-11.html index.html
git commit -m "add 2026-11-11 report"
git push
```

只提交生成后的 `reports/*.html` 和根目录 `index.html`。`data/` 留在本地，不进入 GitHub。

### 注意

- 仓库保持 **public** 最省事；private 仓库的 Pages 取决于 GitHub 计划。
- 不要把 `data/` 里的 PDF、审稿 JSON、API 原始响应提交上去。
- `assets/mathjax/tex-svg.js` 约 2 MB，必须提交，否则线上公式不渲染。
- 如果以后换自定义域名，在 Pages 设置里配置并添加 `CNAME` 文件。
- 已添加 `.nojekyll`，避免 GitHub Pages 的 Jekyll 处理干扰静态资源。

## 边界

- 不把 11-06 的 arXiv 批次写成 11-09“今日新增”；
- 不把摘要写成全文精读；
- 重要性是编辑判断，不是引用数/期刊影响因子；
- APS DOI 页面截稿时未上线的条目，直接用 arXiv 版本阅读并在 venue 里注明；
- 公式必须在数据里显式标记；未标记的公式会让 build_report.py 直接失败。
