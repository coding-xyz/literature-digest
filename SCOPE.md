# 检索范围

> **机器可读配置**：修改下面 JSON 块后，运行 `python scripts\collect.py` 会自动同步到 `config/scope.json`；prose 只作说明。网站、分类、关键词、期刊列表都以这个块为准。

<!-- SCOPE_CONFIG
{
  "arxiv_categories": [
    "quant-ph",
    "cs.ET"
  ],
  "include_keywords": [
    "quantum error correction",
    "fault-tolerant",
    "fault tolerant",
    "surface code",
    "qLDPC",
    "quantum LDPC",
    "logical qubit",
    "magic state",
    "lattice surgery",
    "transpilation",
    "compilation",
    "decoder",
    "decoding",
    "syndrome",
    "noise characterization",
    "crosstalk",
    "leakage",
    "tomography",
    "superconducting",
    "transmon",
    "fluxonium",
    "tunable coupler",
    "circuit quantization",
    "circuit QED",
    "normal mode",
    "capacitance matrix",
    "master equation",
    "lindblad",
    "magnus",
    "1/f noise",
    "control pulse",
    "pauli propagation",
    "pauli frame",
    "pauli truncation",
    "stabilizer simulation",
    "circuit-level noise",
    "detector error model",
    "large-scale simulation"
  ],
  "exclude_keywords": [
    "retraction",
    "erratum",
    "correction",
    "comment on",
    "reply to",
    "book review",
    "jobs",
    "meeting",
    "workshop"
  ],
  "nature_feeds": {
    "Nature": "https://www.nature.com/nature.rss",
    "Nature Physics": "https://www.nature.com/nphys.rss",
    "Nature Communications": "https://www.nature.com/ncomms.rss",
    "npj Quantum Information": "https://www.nature.com/npjqi.rss",
    "Communications Physics": "https://www.nature.com/commsphys.rss",
    "Nature Electronics": "https://www.nature.com/natelectron.rss",
    "Nature Materials": "https://www.nature.com/nmat.rss",
    "Nature Nanotechnology": "https://www.nature.com/nnano.rss"
  },
  "pr_journals": {
    "PRX Quantum": "2691-3399",
    "Physical Review X": "2160-3308",
    "Physical Review Research": "2643-1564",
    "Physical Review Letters": "0031-9007",
    "Physical Review A": "2469-9926",
    "Physical Review Applied": "2331-7019",
    "Reviews of Modern Physics": "0034-6861"
  },
  "extra_journals": {
    "scienceadv": {
      "enabled": true,
      "label": "Science Advances",
      "issn": "2375-2548"
    },
    "scipost": {
      "enabled": true,
      "label": "SciPost Physics",
      "issn": "2542-4653"
    },
    "avs": {
      "enabled": true,
      "label": "AVS Quantum Science",
      "issn": "2639-0213"
    },
    "qst": {
      "enabled": true,
      "label": "Quantum Science and Technology",
      "issn": "2058-9565"
    }
  },
  "quantum_feed": "https://quantum-journal.org/feed/",
  "eprint_feed": "https://eprint.iacr.org/rss/rss.xml",
  "eprint_enabled": true,
  "lookback_days": 7
}
-->

## 容错量子计算设计

### 码与界

- qLDPC、quantum Tanner code、expander code、surface code、color code、topological code。
- rate-distance tradeoff、code bounds、encoding rate、code distance、transversal/addressable gates、code equivalence、logical gate synthesis。
- magic state、distillation、cultivation、magic-state factory、injection、overhead、resource theory。

### 解码与阈值

- circuit-level threshold、single-shot decoding、decoder complexity、decoder-aware code design。
- qLDPC decoder、BP+OSD、Relay-BP、matching、union-find、ML decoder。
- syndrome extraction、circuit-level noise、detector error model、real-time decoding。

### 容错资源、逻辑操作与编译

- lattice surgery、code deformation、code switching、patch connection、logical operation scheduling。
- fault-tolerant compilation、transpilation、routing、distributed quantum computing、CNOT+T / Clifford+T、magic state preparation。
- FT 电路验证、space-time overhead、resource overhead。

### 噪声模型与容错证明

- biased noise、erasure、leakage、correlated noise、non-Markovian noise、adversarial noise。
- adversarial vs stochastic circuit-level noise、threshold proof、single-shot fault tolerance、hook errors、measurement errors。
- noise-adapted codes/decoders、error budget、tomography、randomized benchmarking。

### 容错实验

- logical qubit、repeated syndrome extraction、mid-circuit measurement、erasure detection、dual-rail qubit。
- real-time decoding、fault-tolerant experiment、FT 控制与校准。

## 超导量子计算机模拟仿真

### 芯片设计与电路量子化

- superconducting qubit、transmon、fluxonium、tunable coupler、circuit QED。
- circuit quantization、black-box quantization、normal modes、capacitance/inductance matrix、junction、electromagnetic simulation、finite-element、chip-level crosstalk。
- tensor network、MPS/MPO、DMRG、low-lying spectrum、chip design。

### 测控、开放系统与测量理论

- control pulse、DRAG、KAM、pulse optimization、calibration、flux crosstalk、AC Stark、Autler–Townes。
- input-output theory、dressed master equation、Lindblad、Novikov、Magnus、1/f noise、correlated noise、measurement backaction、quantum trajectories。
- readout、dispersive readout、Purcell filter、Floquet drive、optimal control、parameter estimation、digital twin、real-time feedback。

### 纠错线路的大规模仿真（重点）

- Pauli propagation、Pauli frame、Pauli truncation、stabilizer simulation、Clifford simulation、tableau。
- detector error model、circuit-level noise、syndrome extraction simulation、large-scale QEC simulation、decoder simulation。
- rare-event sampling、parallel decoding co-simulation、tensor-network simulation、stabilizer/Clifford simulability。

### 经典模拟与复杂度边界

- 量子线路/采样问题的经典可模拟性、复杂度阈值、近似误差界。
- 与 FTQC 或超导仿真有方法重叠的数值方法、benchmark 和经典基线。

## 边界

- 量子算法、量子机器学习、量子优化、量子化学、量子计量、量子网络、量子密码。
- 只保留与上述方向有**方法重叠**的工作：例如为大规模线路仿真提供新的经典模拟方法、为编译器/解码器提供 benchmark、为芯片设计提供可迁移的数值方法。
- 纯应用演示、纯优势主张、与 FTQC/超导仿真无方法连接的工作不进入主列表。

## 排除

- 新闻、评论、书评、更正、撤稿、招聘、会议通知。
- 纯经典编码/译码理论，且未涉及量子码、量子线路或量子解码。
- 纯材料生长、器件工艺、微波腔设计，且不涉及电路量子化、芯片级仿真或测控。
- 纯量子优势/采样实验，但没有噪声、损耗、经典基线或可扩展性分析。
- 无法核实 DOI、日期、作者或原文的条目。

---

## 检索网址

### 预印本

| 入口 | 直接网址 | 用途 |
|---|---|---|
| arXiv quant-ph 最新 | https://arxiv.org/list/quant-ph/recent | 每日主列表 |
| arXiv API | https://export.arxiv.org/api/query?search_query=cat:quant-ph&sortBy=submittedDate&sortOrder=descending&max_results=100 | 自动抓取 |
| arXiv 搜 容错 | https://arxiv.org/search/?searchtype=all&query=%22quantum+error+correction%22+OR+%22fault-tolerant%22&start=0 | 纠错/容错 |
| arXiv 搜 解码 | https://arxiv.org/search/?searchtype=all&query=%22quantum+decoder%22+OR+%22single-shot+decoding%22+OR+%22circuit-level+threshold%22&start=0 | 解码/阈值 |
| arXiv 搜 芯片 | https://arxiv.org/search/?searchtype=all&query=%22circuit+quantization%22+OR+%22superconducting+qubit%22+simulation&start=0 | 芯片/电路量子化 |
| arXiv 搜 测控 | https://arxiv.org/search/?searchtype=all&query=%22crosstalk%22+OR+%22control%22+%22superconducting+qubit%22&start=0 | 测控/动力学 |
| arXiv 搜 大规模仿真 | https://arxiv.org/search/?searchtype=all&query=%22Pauli+propagation%22+OR+%22Pauli+frame%22+OR+%22circuit-level+simulation%22&start=0 | 大规模仿真 |
| Cryptology ePrint | https://eprint.iacr.org/ | 仅边界：量子密码/后量子密码 |

### 完全开放获取期刊

| 期刊 | 直接网址 | 更新入口 |
|---|---|---|
| Quantum | https://quantum-journal.org/ | https://quantum-journal.org/feed/ |
| PRX Quantum | https://journals.aps.org/prxquantum/ | https://api.crossref.org/journals/2691-3399/works?filter=from-pub-date:2026-11-01&rows=50&sort=published&order=desc |
| PRX | https://journals.aps.org/prx/ | https://api.crossref.org/journals/2160-3308/works?filter=from-pub-date:2026-11-01&rows=50&sort=published&order=desc |
| Physical Review Research | https://journals.aps.org/prresearch/ | https://api.crossref.org/journals/2643-1564/works?filter=from-pub-date:2026-11-01&rows=50&sort=published&order=desc |
| npj Quantum Information | https://www.nature.com/npjqi/ | https://www.nature.com/npjqi.rss |
| Nature Communications | https://www.nature.com/ncomms/ | https://www.nature.com/ncomms.rss |
| Science Advances | https://www.science.org/journal/sciadv | https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv |
| SciPost Physics | https://scipost.org/SciPostPhys | 主页检索（站点有反爬，人工打开） |
| Communications Physics | https://www.nature.com/commsphys/ | https://www.nature.com/commsphys.rss |
| AVS Quantum Science | https://pubs.aip.org/avs/aqs | 主页检索（以期刊页的 OA 标识为准） |

### 核心同行评审期刊（部分 OA）

| 期刊 | 直接网址 |
|---|---|
| Physical Review Letters | https://journals.aps.org/prl/ |
| Physical Review A | https://journals.aps.org/pra/ |
| Physical Review Applied | https://journals.aps.org/prapplied/ |
| Nature Physics | https://www.nature.com/nphys/ |
| Nature | https://www.nature.com/nature/ |
| Quantum Science and Technology | https://iopscience.iop.org/journal/2058-9565 |

---

> 抓取按 7 天滚动窗口；当日没有新批次时明确标“无当日更新”，保留最近批次。自动抓取入口优先使用 arXiv API、Crossref 和 RSS。
