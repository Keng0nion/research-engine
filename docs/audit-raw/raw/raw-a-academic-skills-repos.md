审计完成。以下是完整报告。

---

# Research Engine v2 Stage 1+2 仓库审计报告

审计日期：2026 年 11 月 17 日。审计纪律遵守情况：全程只读。两个仓库均以 `git clone --depth 1` 拉到 /tmp/re-audit/（分别 67MB 与 62MB，均在 100MB 阈值内），未运行仓库内任何脚本，未执行 npm/pip install，未执行任何仓库代码。元数据来自 `gh api`，部分单文件来自 raw.githubusercontent.com。所有事实均可回溯到读到的文件内容；凡未读到的写「未验证」。

---

## YuanyuanMa03/academic-research-skills

- URL：https://github.com/YuanyuanMa03/academic-research-skills
- stars：79（缓存于 /tmp/re-audit/academic-research-skills，克隆于 2026 年 11 月 17 日）
- license：MIT。许可证文件路径 `/LICENSE`（21 行，Copyright (c) 2025 YuanyuanMa03）；GitHub API `license.spdx_id` 返回 "MIT"。无第三方归属文件。
- 最近提交：2026 年 10 月 29 日 05:36:23 UTC，作者 YYMa（GitHub 登录名 YuanyuanMa03），提交信息为「Merge pull request #8 from YuanyuanMa03/fix/round3-optimize」。
- releases：2 个。最新 tag `v2.0.0`（发布于 2026 年 10 月 29 日 04:35 UTC）；另有 `v1.2.0`（同日 02:15）。仓库 tag 列表与 releases 一致。
- open issues：1 个（#4「fix(nature-academic-search): start the MCP server on Windows and install missing deps」，2026 年 9 月 27 日开）。
- 其他：创建于 2026 年 6 月 6 日；默认分支 main；未归档。注意：CHANGELOG.md 顶部版本段落写 [2.0.1]，但 releases 最新 tag 为 v2.0.0，两者不一致（CHANGELOG 未对应建 tag）。

### 实际内容清单（全部 16 个 SKILL.md）

结构为 plugins/<插件>/skills/<技能>/SKILL.md，16 个插件与 16 个 SKILL.md 一一对应：

| # | SKILL.md 路径 | 一句话用途 |
|---|---|---|
| 1 | plugins/cnki-search/skills/cnki-search/SKILL.md | CNKI 全流程：关键词检索、高级检索（作者/期刊/日期/核心库过滤）、论文详情解析、翻页、期刊检索/目录/导航（另有 7 个 references 子流程文档） |
| 2 | plugins/nature-academic-search/skills/nature-academic-search/SKILL.md | 多源文献检索、引文校验、MeSH 检索策略、.nbib/.ris/.bib 转换、参考文献管理，走自带 MCP server（PubMed、CrossRef、arXiv，另含 Scopus、ScienceDirect 源） |
| 3 | plugins/nature-citation/skills/nature-citation/SKILL.md | 稿件文本分段补 Nature/CNS 系严格引文，只检索 Nature Portfolio、Science 系、Cell Press 标题，导出 EndNote/RIS/Zotero RDF 或 GB/T 7714 中文格式 |
| 4 | plugins/nature-data/skills/nature-data/SKILL.md | Nature 风格数据可用性声明、数据仓库规划、数据集引用、FAIR 元数据清单 |
| 5 | plugins/nature-figure/skills/nature-figure/SKILL.md | 投稿级图表工作流（强制先选 Python 或 R；matplotlib/seaborn 或 ggplot2/patchwork/ComplexHeatmap），含出图后 QA |
| 6 | plugins/nature-paper-to-patent/skills/nature-paper-to-patent/SKILL.md | 论文/报告/源码转中文发明专利草案（权项、说明书、摘要、附图；公式保留为 Office Math；DOCX 出具） |
| 7 | plugins/nature-paper2ppt/skills/nature-paper2ppt/SKILL.md | 论文转 Nature 风格中文 PPTX（识别论文类型、选图、写讲稿、生成 .pptx、自审修订循环） |
| 8 | plugins/nature-polishing/skills/nature-polishing/SKILL.md | 按 Nature 写作策略与 Academic Phrasebank 润色、重构、中译英 |
| 9 | plugins/nature-reader/skills/nature-reader/SKILL.md | 全文中英对照、图表就位、带源锚点的 Markdown 精读文档（不许退化为摘要） |
| 10 | plugins/nature-response/skills/nature-response/SKILL.md | 大修/小修审稿意见逐点回复信起草与修订（含中文场景） |
| 11 | plugins/nature-reviewer/skills/nature-reviewer/SKILL.md | Nature 风格审稿人视角预审：3 份审稿报告 + 交叉综合 |
| 12 | plugins/nature-writing/skills/nature-writing/SKILL.md | 按 Nature 风格起草/重构摘要、引言、结果叙述、讨论、结论、题目 |
| 13 | plugins/pm-search/skills/pm-search/SKILL.md | PubMed 精确 API 检索，返回 PMID、标题、作者、期刊、日期、DOI 结构化结果（双路径：Python 脚本优先，浏览器兜底） |
| 14 | plugins/scansci-pdf/skills/scansci-pdf/SKILL.md | 论文获取枢纽，桥接外部 scansci-pdf MCP：多路由 PDF 下载（开放获取→出版商 API→机构通道竞速）、批量清单、引文导出、推送 Zotero、机构登录、诊断排障 |
| 15 | plugins/sd-search/skills/sd-search/SKILL.md | ScienceDirect 全流程：关键词/高级检索、详情解析、结果页解析、翻页、期刊浏览（5 个 references 子流程） |
| 16 | plugins/wos-search/skills/wos-search/SKILL.md | Web of Science 全流程：主题/作者/标题/DOI/高级检索（内部 API 含 SID 回退）、详情解析、离线快照解析、翻页、DOM 参考（4 个 references） |

任务书点名核实（第一个仓库）：

| 点名项 | 结论 |
|---|---|
| cnki-search | 存在（plugins/cnki-search，v2.0.0） |
| nature-academic-search | 存在（v1.0.3） |
| pm-search | 存在（v1.0.1） |
| sd-search | 存在（v2.0.0） |
| wos-search | 存在（v2.0.0） |
| gs-search | 不存在。CHANGELOG.md 2.0.0 段明确记录：`gs-*` 4 个插件因 2026 年 6 月测试超时且未恢复被整体移除；`plugins/` 下无该目录，两个 marketplace.json 的插件列表也无它。但 README.md 第 139 行、README_zh.md 第 137 行仍保留陈旧安装命令 `codex plugin add gs-search@academic-research-skills`，.claude-plugin/marketplace.json 描述里也仍写 Google Scholar，属文档残留 |
| scansci-pdf | 存在（plugins/scansci-pdf，plugin.json 版本 1.0.1） |
| Zotero 集成 | 无独立 Zotero 技能（旧 `zotero-csl` 于 v1.2.0 随 6 个重复 push_to_zotero.py 一起移除）。现存两条路径：（a）nature-citation 脚本可导出 Zotero RDF 文件（离线，无需 key）；（b）scansci-pdf 的 `scansci_pdf_zotero_push` 走 Zotero Web API，需 zotero.org 的 API key，明确不是本地 Zotero 客户端 |

### 脚本情况（每个技能是否自带脚本、语言、依赖）

- 根 `/scripts/` 4 个 Python 维护脚本（check_marketplace_consistency.py、check_shared_assets.py、validate_plugin_json.py、validate_skills.py），供 CI 与 pre-commit 用，不是技能运行脚本。
- 带脚本的技能（按实测目录）：
  - nature-academic-search：自带完整 MCP server 实现（mcp-server/academic_search_server.py 397 行 + sources 6 个源 + utils 3 个，共 2201 行）+ scripts 5 个（academic_search.py 430 行 OpenAlex 兜底、converters.py、format-converter.py 522 行、preflight.py、run_academic_search_mcp.py venv 引导）。第三方依赖：mcp、requests、toml、lxml、pybliometrics（plugins/nature-academic-search/skills/nature-academic-search/mcp-server/requirements.txt）。
  - nature-citation：scripts/nature_citation.py 2116 行。纯 Python 标准库（urllib、xml.sax、csv、hashlib 等），只访问 api.crossref.org。
  - nature-paper-to-patent：8 个 Python 脚本；依赖 python-docx、pypdf、latex2mathml、Pillow（其 requirements.txt）。
  - nature-figure：assets/figures4papers/ 下约 29 个示例绘图脚本（matplotlib/seaborn），属参考素材而非技能必须执行件。
  - pm-search：scripts/pubmed_api_search.py 336 行。纯标准库 urllib，脚本内自带 `https` 强制与 NCBI 主机白名单（ALLOWED_HOSTS），并有针对该门禁的单测。
- 无脚本（纯提示词 + references/static 文档）的 9 个：nature-writing、nature-polishing、nature-reader、nature-reviewer、nature-response、nature-data、nature-paper2ppt、cnki-search、sd-search、wos-search 中的浏览器型在后文单列；其中 nature-paper2ppt 的 static/core/toolchain.md 要求 agent 现场写 PyMuPDF/Pillow/python-pptx 代码，但仓库不交付脚本。
- 语言统计（find 全仓）：60 个 .py、1 个 .sh（nature-academic-search/install.sh）、0 个 js/ts。

### 依赖与运行要求（纯提示词 / 浏览器 / CLI / API）

- 纯提示词型：9 个 nature-* 写作技能（README 原话「Nature skills are pure prompt-based and work with any LLM」），零运行时依赖。
- 脚本型：pm-search、nature-citation 只需 Python 3（标准库）与联网；nature-paper-to-patent 需 pip 装 4 个库；nature-figure 需 Python（matplotlib/seaborn）或 R（ggplot2 等）运行时。
- MCP 型：
  - nature-academic-search：宿主需支持 MCP；自带 .mcp.json 用 python3 直接跑 run_academic_search_mcp.py，首次运行自动在 `~/.cache/academic-search-mcp` 建 venv 并 pip 安装 4 个依赖（这是真实存在的自动装包行为，代码在 run_academic_search_mcp.py）。另有 install.sh 会写 `~/.claude`（拷 server、合并 .mcp.json、改 settings.json 的 enabledMcpjsonServers）。
  - scansci-pdf：需宿主 MCP + 本机 `pip install scansci-pdf`（Python ≥ 3.11）；可选浏览器后端 `pip install "scansci-pdf[camoufox]"`（不装则只能下 OA 仓库直链型文章）；机构登录场景必须装。
- 浏览器型：cnki-search、sd-search、wos-search 依赖 chrome-devtools MCP。三个插件各自的 .mcp.json 完全一致：`npx chrome-devtools-mcp@latest --ignoreDefaultChromeArg=--enable-automation --ignoreDefaultChromeArg=--disable-infobars --chromeArg=--disable-blink-features=AutomationControlled`。即需要本机有 node/npx、并驱动用户日常已登录的 Chrome。wos-search 明确要求浏览器已处于 webofscience.com 登录态（直接 fetch 内部 API，靠 SID）；cnki-search 要求用户手动过滑块验证；sd-search 可能撞 Elsevier 的 Cloudflare 挑战。

### 认证与成本

- pm-search：NCBI E-utilities 免费公开 API，无 key，无需登录；可选 `--mailto` 或 NCBI_MAILTO 进礼貌池。成本为零。
- nature-citation：Crossref API 免费，可选 `--mailto`。成本为零。
- nature-academic-search：PubMed、CrossRef、arXiv 免费（可选 NCBI_API_KEY 提升限额，config.toml 默认留空）；Scopus 与 ScienceDirect 两个源经 pybliometrics 实现，需 Elsevier API key（代码 elsevier_common.py 在 pybliometrics 配置文件缺失时直接报 DataSourceError），属付费/机构凭证。
- scansci-pdf：软件 MIT 免费；但 Unpaywall 需真实邮箱；Zotero 推送需 Zotero Web API key；机构通道需机构订阅且出口 IP 在校园网段（SKILL.md 明说系统代理会静默作废 IP 认证）；Sci-Hub/LibGen 灰色源需用户明确选择。
- cnki-search、sd-search、wos-search：无 API key 概念，依赖用户已有平台登录态与机构订阅。

### 安全观察

- 网络行为面：全仓扫描出的外联主机全部是学术与平台域名（kns.cnki.net、link.cnki.net、navi.cnki.net、eutils.ncbi.nlm.nih.gov、api.crossref.org、export.arxiv.org、api.openalex.org、elsevier.com、webofscience.com 等），未见任何向无关第三方回传数据的代码；未见 base64 混淆、exec/eval 动态执行用户输入、凭据文件读取（`.ssh`/`.aws`/`.netrc` 均无命中）。
- 凭据写入：核心脚本不写入凭据；凭据存放都在用户侧（pybliometrics 自己的配置、Zotero key 由用户给）。scansci-pdf SKILL.md 明确要求把 API key、cookie、代理凭据视为机密不在回复中复述。
- 自动化改写宿主配置（需知悉）：nature-academic-search 的 install.sh 会往 `~/.claude/settings.json` 写 enabledMcpjsonServers；run_academic_search_mcp.py 会在首次运行时自动 pip install 到用户 cache 目录。均为常规安装自动化，但属「安装即改宿主配置」一类，建议人工审阅后手动执行。
- 合规风险（重点）：cnki-search、sd-search、wos-search 本质是带反检测开关的浏览器自动化抓取平台页面与内部 API（wos-search 直接调用 Web of Science 内部接口并用会话 SID）。CHANGELOG 2.0.1 段自述：CNKI 加载即出滑块墙、ScienceDirect 加载即出 Cloudflare「Are you a robot?」，自动化 webview 上下文会被立刻指纹识别，因此技能要求改用用户日常 Chrome 并注入 `--disable-blink-features=AutomationControlled`。这类反检测手段大概率违反相应平台服务条款（平台 ToS 原文未获取，属推断，未验证）。
- scansci-pdf 支持 Sci-Hub/LibGen（默认 `fastest` 全源竞速，可切 `legal_only`）。法律风险由使用者承担，SKILL.md 本身也有合规边界章节。
- 许可证兼容性：仓库自身 MIT，可自由使用。唯一桥接的外部项目 scansci-pdf 上游我已单独核实：raw.githubusercontent.com 拉取其 LICENSE 返回 MIT 全文（Copyright (c) 2024-2026 scansci-pdf contributors）。chrome-devtools-mcp（npm 包）的许可证与行为未核实。
- 结论：仓库一在我读到的范围内未见恶意行为；风险集中在「浏览器反检测的合规性」与「灰色源下载」两处，属使用者决策问题。

### 结论（四类归类与推荐纳入清单）

| 技能 | 归类 |
|---|---|
| pm-search、nature-citation | 可独立运行（stdlib 脚本 + 免费 API） |
| nature-writing、nature-polishing、nature-reader、nature-reviewer、nature-response、nature-data、nature-paper2ppt | 可独立运行（纯提示词） |
| nature-figure、nature-paper-to-patent | 可独立运行（需本机 Python 或 R 运行时与若干 pip 包） |
| cnki-search、sd-search、wos-search | 需浏览器依赖（chrome-devtools MCP + 已登录浏览器 + 机构订阅） |
| nature-academic-search | 需 MCP 依赖（免费源部分可用；Scopus/ScienceDirect 部分需付费凭证） |
| scansci-pdf | 需 MCP 依赖（+ 可选浏览器后端；机构通道需机构凭证） |

推荐纳入本项目：一、nature-citation（首选，GB/T 7714 中文引文与 Nature/CNS 定向补引，stdlib 零依赖）；二、pm-search（首选，PubMed 精确 API 双路径，距离 v2 的文献引擎最近）；三、nature-* 写作组按需吸收（纯提示词，零成本，nature-reader 的对照精读与 nature-reviewer 的预审最实用）；四、cnki-search 仅在确有 CNKI 订阅需求且接受浏览器自动化合规风险时纳入；五、scansci-pdf、sd-search、wos-search 建议缓纳，若纳入只开 legal_only 并接受重依赖。整体价值中等偏上，价值集中在 PubMed 检索、中文引文、Nature 写作三个点，而非平台抓取。

---

## KalarisLabs/research-agent-skills

- URL：https://github.com/KalarisLabs/research-agent-skills
- stars：153
- license：GitHub 标记 NOASSERTION。许可证文件路径 `/LICENSE`，实际条款我已打开逐段读完：正文为标准 MIT 文本（Copyright (c) 2026 Kalaris Labs），文末追加一段说明「Portions of the skills in skills/ are adapted from third-party MIT-licensed projects; see THIRD_PARTY_NOTICES.md and LICENSES/」。`/LICENSES/` 下两份上游声明：MIT-upstream-a.txt（Copyright (c) 2025 K-Dense Inc.）、MIT-upstream-b.txt（Copyright (c) 2025 Claude AI Research Skills Contributors），均为标准 MIT。`/THIRD_PARTY_NOTICES.md` 载明来历与 pin 的 revision：159 个技能来自 K-Dense-AI/scientific-agent-skills（revision 65d6e786832e）、98 个来自 orchestra-research/AI-research-SKILLs（revision 773a52944ba4）。
  - 关键限制（逐条简述）：（1）唯一实质义务是保留版权与许可声明（MIT 通例）；（2）THIRD_PARTY_NOTICES.md 明确声明「个别技能可能含按自身条款分发的材料（例如出版商的 LaTeX 模板），或技能 frontmatter 中 license 字段写明其记录的软件的许可证），那些条款另行适用」——即整仓 MIT 不覆盖技能内可能夹带的第三方素材，使用具体技能前需查该技能目录内声明；（3）我核实了 frontmatter 的 license 字段分布：230 个技能写 MIT、13 个 BSD-3-Clause、7 个 Apache-2.0、3 个 GPL 系（GPL-2.0、GPL-3.0-or-later、GPLv3，分别对应 bioservices、cobrapy 等被记录的软件本身）、1 个「Proprietary (API key required)」（rowan）——这些描述的是「该技能所记录的软件」的许可证，不改变仓库自身内容的 MIT 属性。对在本机自由使用无阻碍。
- 最近提交：2026 年 11 月 13 日 18:15:41 UTC，作者 kalarislabs（GitHub 登录名 kalaris-labs），提交信息「Update README.md」。
- releases：1 个。最新 tag `v1.1.1`（发布于 2026 年 10 月 4 日）；tags 另有 `v1.1.0`（未建 release，无发布记录）。
- open issues：56 个。抽查最近 10 条（#2006 至 #2015）全部是自动生成的「Add docstring to ...」类小问题，低严重度。
- 其他：创建于 2026 年 7 月 7 日；默认分支 main；未归档。

### 实际内容清单

- 总量：`skills/` 下 281 个目录，281 个 SKILL.md（find 计数逐一对上）。
- 每个技能自带工件：115 个技能带 scripts/ 目录；skills/ 内共 506 个 .py、2 个 .sh、2 个 .js 脚本。另有 283 个 evals/ 目录（逐技能 evals.json）。
- 仓库自带 27 个分类清单（catalog/lists/，合计覆盖全部 281 项），与本项目相关的类别计数：literature-review 18、research-writing 15、scientific-databases 12、journal-formats 11、ideation-and-design 12、research-automation 9、research-essentials 67（跨类合集）等。
- 全部 281 个技能名（catalog/lists/all.txt 原文，逐一列出）：
  13c-metabolic-flux, abstract-and-title, academic-plotting, acm-sigconf, adaptyv, aeon, alphagenome, analytical-method-validation, anndata, apa7, ara-compiler, ara-research-manager, ara-rigor-reviewer, arbor, arboreto, arxiv-submission, astropy, audiocraft-audio-generation, autogpt-agents, autoresearch, autoskill, awq-quantization, axolotl, benchling-integration, bgpt-paper-search, bibtex-hygiene, bids, biopython, bioservices, blip-2-vision-language, brainstorming-research-ideas, bulk-rnaseq, cell-press, cellxgene-census, chroma, cirq, citation-management, citation-verification, clinical-decision-support, clinical-reports, clip, cobrapy, consciousness-council, constitutional-ai, cover-letter-to-editor, creative-thinking-for-research, crewai-multi-agent, dask, database-lookup, datalad, datamol, deepchem, deepspeed, deeptools, depmap, dhdna-profiler, diffdock, distributed-llm-pretraining-torchtitan, dnanexus-integration, dspy, elsevier-cas, esm, etetoolkit, evaluating-code-models, evaluating-cosmos-policy, evaluating-llms-harness, evolving-ai-agents, exa-search, experiment-tracking-swanlab, experimental-design, exploratory-data-analysis, faiss, fictiv, fine-tuning-openvla-oft, fine-tuning-serving-openpi, fine-tuning-with-trl, firecrawl-research-index, flowio, fluidsim, folklore-variant-evidence, generate-image, geniml, genomic-coordinates, genomic-intelligence, geomaster, geopandas, get-available-resources, gget, gguf-quantization, ginkgo-cloud-lab, gptq, grpo-rl-training, gtars, guidance, histolab, hqq-quantization, hugging-science, huggingface-accelerate, huggingface-tokenizers, hypogenic, hypothesis-generation, ieee-transactions, imaging-data-commons, implementing-llms-litgpt, infographics, instructor, iso-standards-readiness, knowledge-distillation, lab-hardware-cad, labarchive-integration, lambda-labs-gpu-cloud, lamindb, langchain, langsmith-observability, latchbio-integration, latex-posters, liteparse, literature-review, llama-cpp, llama-factory, llamaguard, llamaindex, llava, long-context, mamba-architecture, markdown-mermaid-writing, market-research-reports, markitdown, matchms, matlab, matplotlib, medchem, miles-rl-training, ml-paper-writing, ml-training-recipes, mlflow, modal, modal-serverless-gpu, model-merging, model-pruning, moe-training, molecular-dynamics, molfeat, nanogpt, nature-portfolio, ncats-arax, nemo-curator, nemo-evaluator-sdk, nemo-guardrails, networkx, neurokit2, neuropixels-analysis, nextflow, nnsight-remote-interpretability, omero-integration, onekgpd, ontology-term-resolution, open-notebook, openpiv, openrlhf-training, opentrons-integration, optimize-for-gpu, optimizing-attention-flash, outlines, pacsomatic, paper-corpus-rag, paper-lookup, paperclip, paperzilla, parallel-web, pathml, pathogen-variant-surveillance, pathway-enrichment, peer-review, peft-fine-tuning, pennylane, phoenix-observability, pi-agent, pinecone, pkpd-modeling, plos, polars, polars-bio, pptx-posters, presenting-conference-talks, prompt-guard, protocolsio-integration, pufferlib, pydeseq2, pydicom, pyhealth, pylabrobot, pymatgen, pymc, pymoo, pyopenms, pysam, pytdc, pytorch-fsdp2, pytorch-lightning, pytorch-lightning-distributed, pyvene-interventions, pyzotero, qdrant-vector-search, qiskit, quantizing-models-bitsandbytes, qutip, ray-data, ray-train, rdkit, rebuttal-and-response-to-reviewers, reference-manager-interop, relsa-severity-assessment, reproducibility-statement, research-agent-skills, research-grants, research-knowledge-graph, research-lookup, research-skill-creator, rowan, rwkv-architecture, scanpy, scholar-evaluation, science-aaas, scientific-brainstorming, scientific-critical-thinking, scientific-schematics, scientific-slides, scientific-visualization, scientific-writing, scikit-bio, scikit-learn, scikit-survival, scvelo, scvi-tools, seaborn, segment-anything-model, sentence-transformers, sentencepiece, serving-llms-vllm, sglang, shap, simpo-training, simpy, skypilot-multi-cloud-orchestration, slime-rl-training, sparse-autoencoder-training, speculative-decoding, springer-lncs, stable-baselines3, stable-diffusion-image-generation, statistical-analysis, statistical-power, statsmodels, sympy, systematic-review-prisma, systems-paper-writing, tamarind, tensorboard, tensorrt-llm, tiledbvcf, timesfm-forecasting, torch-geometric, torchdrug, torchforge-rl-training, training-llms-megatron, transformer-lens-interpretability, transformers, treatment-plans, umap-learn, uncertainty-and-units, unslop-academic-writing, unsloth, usfiscaldata, vaex, venue-templates, verl-rl-training, waypoint-bio, weights-and-biases, whisper, zarr-python。
- 与本项目相关的类目清单（名称原文）：literature-review 18 项 = bgpt-paper-search, bibtex-hygiene, citation-management, citation-verification, exa-search, firecrawl-research-index, liteparse, literature-review, markitdown, open-notebook, paper-lookup, paperclip, paperzilla, parallel-web, pyzotero, reference-manager-interop, research-lookup, systematic-review-prisma；research-writing 15 项 = abstract-and-title, cover-letter-to-editor, dhdna-profiler, markdown-mermaid-writing, market-research-reports, ml-paper-writing, peer-review, rebuttal-and-response-to-reviewers, reproducibility-statement, research-grants, scholar-evaluation, scientific-critical-thinking, scientific-writing, systems-paper-writing, unslop-academic-writing；journal-formats 11 项 = acm-sigconf, apa7, arxiv-submission, cell-press, elsevier-cas, ieee-transactions, nature-portfolio, plos, science-aaas, springer-lncs, venue-templates；scientific-databases 12 项 = bioservices, cellxgene-census, database-lookup, depmap, genomic-coordinates, gget, imaging-data-commons, ncats-arax, onekgpd, ontology-term-resolution, pytdc, usfiscaldata。

任务书点名核实（第二个仓库，7 项全部存在）：

| 点名项 | 结论与实测路径 |
|---|---|
| paper-lookup | 存在。skills/paper-lookup/SKILL.md（295 行，name: paper-lookup，version 2.2），搜索 18 个学术 API，带 5 个 stdlib 脚本（_common.py、paginate.py、jats_to_text.py、arxiv_atom.py、openalex_abstract.py） |
| research-lookup | 存在。skills/research-lookup/SKILL.md（341 行，version 1.5），默认走 Parallel Search/Extract/Research，脚本 2 个（research_lookup.py、manuscript_packet.py） |
| database-lookup | 存在。skills/database-lookup/SKILL.md（396 行，version 1.6），无脚本，references/ 82 个文件（含 database_selection_guide.md 与 addgene、alphafold、alphavantage、bindingdb、biogrid、bls、brenda、cbioportal、chebi、chembl、clinicaltrials、clinpgx、clinvar、cod、cosmic、dailymed、datacommons、dbsnp、disgenet、drugbank、ecb、emdb、ena、encode、ensembl、epa、eurostat 等逐库文档） |
| literature-review | 存在。skills/literature-review/SKILL.md（294 行，version 1.8），scripts 5 个（search_databases.py、verify_citations.py、generate_pdf.py、generate_schematic.py、generate_schematic_ai.py） |
| systematic-review-prisma | 存在。skills/systematic-review-prisma/SKILL.md（118 行，version 1.0，author Kalaris Labs (Sayan Chowdhury)），scripts 2 个（dedupe_records.py、prisma_flow.py），纯标准库 |
| citation-verification | 存在。skills/citation-verification/SKILL.md（82 行，version 1.0），scripts/verify_citations.py（372 行，纯标准库 urllib，查 Crossref、OpenAlex、arXiv） |
| scientific-critical-thinking | 存在。skills/scientific-critical-thinking/SKILL.md（211 行，version 1.3），无脚本，references 8 个文件；来源属 K-Dense 上游 159 项之一 |

附带核实（Zotero 相关，任务书未点名但与本项目有关）：pyzotero 存在（skills/pyzotero，需 Python 3.10+ 与 pyzotero 1.13+，frontmatter 声明 ZOTERO_API_KEY 与 ZOTERO_LIBRARY_ID 为 required）；reference-manager-interop 存在（零依赖 BibTeX/RIS/CSL-JSON 转换器）；citation-management 存在（需 requests；Google Scholar 检索额外需 scholarly）。

### 脚本情况（语言与依赖实测）

- paper-lookup：5 个脚本全为 Python 标准库（urllib、json、xml.etree、pathlib、dataclasses），零第三方依赖。已验证无 requests。
- citation-verification：单脚本 372 行，全标准库（argparse、difflib、json、unicodedata、urllib）。
- systematic-review-prisma：2 个脚本标准库（csv、json、unicodedata），Graphviz 仅用于 DOT 渲染可选。
- bibtex-hygiene、reference-manager-interop、unslop-academic-writing：SKILL.md 均自述「零依赖 linter/converter」（标准库）。
- literature-review：verify_citations.py 导入 requests（第三方）；generate_pdf.py 以 subprocess 调 pandoc 可执行文件（并检测 pandoc/XeLaTeX 等是否安装）；generate_schematic_ai.py（957 行）与 generate_schematic.py 走 OpenRouter 图片 API；search_databases.py 标准库。
- research-lookup：research_lookup.py 以 subprocess 调 `parallel-cli`（需另行安装 parallel-cli 0.7.1+），Search/Extract/Research 走 api.parallel.ai，显式 Chat 走 api.parallel.ai 需 PARALLEL_API_KEY，可选 Perplexity 走 openrouter.ai 需 OPENROUTER_API_KEY。
- database-lookup、scientific-critical-thinking：无脚本（提示词 + 参考文档型）。
- 全仓口径：skills/ 内 506 个 .py 中，与学术主线相关的技能普遍是标准库脚本；领域科学技能（rdkit、scanpy 等）的脚本假设使用者环境已装对应软件包，缺失时脚本只打印 `uv pip install ...` 提示文本，不自动安装（我核对了 scikit-survival、pkpd-modeling、qiskit 等多处命中，全部是提示字符串而非执行）。

### 依赖与运行要求

- 纯提示词型：database-lookup、scientific-critical-thinking、unslop-academic-writing、scientific-writing、venue-templates（LaTeX 编译可选）、bibtex-hygiene、reference-manager-interop 等。
- 仅需 Python 标准库 + 联网：paper-lookup、citation-verification、systematic-review-prisma。
- 需第三方依赖：literature-review（requests；PDF 出图需 pandoc）；citation-management（requests，GS 需 scholarly）；pyzotero（pyzotero 包 + Zotero 账号）；research-lookup（parallel-cli 外部 CLI）。
- 需宿主支持：仓库同时交付 Claude Code 插件 marketplace（.claude-plugin/marketplace.json 定义 research-essentials 等 bundle）、Codex 插件（.codex-plugin）、npx 安装器（cli/，npm 包名 research-agent-skills，Node ≥ 18.17）与 Python 安装器（src/research_agent_skills，可 `uvx research-agent-skills install ...`）。

### 认证与成本

- 免费公开 API（无需 key）：paper-lookup 覆盖的 18 个源均有免费路径（references 逐文件核实）：PubMed/PMC/Europe PMC（europepmc.md 原话「None. No key, no email parameter, no registration.」）、bioRxiv/medRxiv、arXiv、OpenAlex、Crossref、Semantic Scholar、OpenCitations、PubTator3、Zenodo、Figshare、ROR、BioStudies、DOAJ；Unpaywall 需真实邮箱参数。可选 key 仅提升限额或解锁：NCBI_API_KEY（3 转 10 次每秒）、S2_API_KEY、CORE_API_KEY、OPENALEX_API_KEY。
- citation-verification：Crossref、OpenAlex、arXiv 全免费，可选 CROSSREF_MAILTO。
- 需付费或账号的（同仓其它技能）：research-lookup（PARALLEL_API_KEY；可选 OPENROUTER_API_KEY）、paperclip（PAPERCLIP_API_KEY）、exa-search（EXA_API_KEY）、firecrawl-research-index（Firecrawl 账号）、paperzilla（账号）、bgpt-paper-search（BGPT MCP）、tamarind、rowan、alphagenome 等。
- 口径统计：20 个技能的 frontmatter 声明 primaryEnv，分布为 OPENROUTER_API_KEY 6 个、PARALLEL_API_KEY 2 个，另有 ZOTERO_API_KEY、TAMARIND_API_KEY、SCREENPIPE_TOKEN、ROWAN_API_KEY、PROTOCOLS_IO_ACCESS_TOKEN、PAPERCLIP_API_KEY、HF_TOKEN、GI_API_KEY、EXA_API_KEY、BENCHLING_API_KEY、ANTHROPIC_API_KEY、ALPHAGENOME_API_KEY 各 1 个；其余技能无强制 key 声明。

### 安全观察

- 自带安全工程（同仓最强项）：`/security/allowed-domains.txt` 是脚本允许联系域名的白名单（约 60 个学术、标准、包托管域名，且注明新增需 CODEOWNERS 复核）；`/security/skill-scanner-baseline.json` 与 `/security/skill-scanner-review-2026-10-01.md` 对 53 条 HIGH/CRITICAL 扫描发现逐条给出人工复核结论（绝大多数为误报：Model.eval() 被当成动态执行、环境变量送往既有 HTTPS 端点被当成外传、Screenpipe token 送往其自配置守护进程等）；CI 有 14 个 workflow，含 CodeQL（code-security.yml）、Cisco skill-scanner 门禁（skill-security.yml）、注入 lint（tools/lint_injection.py）、供应链（supply-chain.yml）、vendor 安全（vendor-security.yml）、OpenSSF Scorecard。
- 我的独立抽查（与官方声明交叉验证）：全仓 skills/ 未见 `curl | sh`、未见 sudo、未见向未知主机 POST；pip install 命中全部是提示文本；唯一的实际网络代码安装是 pacsomatic/scripts/run_pacsomatic.py 在显式传参时 `git clone` 其流水线仓库（属该技能的设计行为，需用户显式触发）；未见 `.ssh`、`.aws`、`.netrc`、keychain 读取；base64 命中 10 个文件均为正常编码用途；安全报告称 8 处计算器示例的 `eval()` 已改为有界算术解析器，与仓内 tests/test_safe_arithmetic_examples.py 的存在一致。
- 两处需知悉的行为：（1）scientific-schematics 等脚本会从当前目录逐级向上查 `.env` 文件，但只读取 OPENROUTER_API_KEY 一项（范围受限，仍属「会读你项目里的 .env」）；（2）autoskill 技能涉及读屏工具 screenpipe 的 token（该技能不在本项目推荐清单内）。
- 遥测：`.github/workflows/posthog-telemetry.yml` 仅上报 CI 与仓库健康（workflow 成败、catalog 统计、每日仓库快照），注释明确「It reports nothing about people who use the skills」，无密钥时全步为空操作；我在 cli/src 与 src 内 grep posthog/telemetry/analytics 未发现客户端遥测代码。
- 许可证兼容性：整仓 MIT（含两处上游 MIT 归属），可在本机自由使用；唯一注意点是 THIRD_PARTY_NOTICES 声明的「个别技能含按自身条款分发的素材（如出版商 LaTeX 模板）」——若深用 venue-templates 之类技能，需查其目录内是否夹带出版商标识材料（我未逐个打开 281 个技能的所有素材文件，此处为已知边界）。
- 结论：在我读到的范围内未见可疑网络行为、未见凭据外传，安全治理水平明显高于同类仓库。

### 结论（四类归类与推荐纳入清单）

| 技能 | 归类 |
|---|---|
| paper-lookup | 可独立运行（stdlib + 18 个免费 API） |
| citation-verification | 可独立运行（零依赖） |
| systematic-review-prisma | 可独立运行（stdlib） |
| scientific-critical-thinking | 可独立运行（纯提示词） |
| database-lookup | 可独立运行（纯提示词；个别目标数据库自身可能需 key，视调用而定） |
| literature-review | 可独立运行（基础路径）；PDF 输出需本机 pandoc、AI 配图需 OPENROUTER_API_KEY（增强步骤可选） |
| research-lookup | 需付费凭证（parallel-cli + PARALLEL_API_KEY） |

推荐纳入本项目（按优先级）：一、paper-lookup（首选，18 源免费 API、零依赖脚本、自带溯源纪律与「200 也失败」陷阱文档，与文献引擎最对口）；二、citation-verification（首选，零依赖、直击 AI 引文幻觉，还带基准）；三、systematic-review-prisma（stdlib 去重 + 拒绝不一致计数的 PRISMA 图生成，中文流程说明齐）；四、bibtex-hygiene 与 reference-manager-interop（零依赖 BibTeX/RIS/CSL-JSON 清洁与互转，正好补 Zotero 生态缺口）；五、database-lookup（82 个数据库端点文档，按需加载）；六、写作组 unslop-academic-writing、scientific-writing、abstract-and-title、venue-templates（若 v2 涉及成稿）；七、pyzotero（若需程序化 Zotero 集成，需 Zotero 账号 key）；八、literature-review（若要端到端综述流水线，接受 requests 与 pandoc 依赖）。不建议优先纳入：research-lookup（付费）、paperclip/paperzilla/exa-search/firecrawl-research-index/bgpt-paper-search（账号或付费）、autoskill（读屏隐私敏感）、其余 200 余个领域科学技能（超出学术引擎范围）。整体价值高，是本审计两个仓库中信息密度与工程完备度更高的一个。

---

## 总结：重叠度、选型与理由

重叠度评估：两仓库在「文献检索、引文管理、写作辅助」三层有实质重叠——repo1 的 pm-search 对照 repo2 的 paper-lookup 与 citation-management（PubMed 与 DOI 元数据检索）；repo1 的 nature-citation 对照 repo2 的 citation-verification 与 bibtex-hygiene（补引与引文治理）；repo1 的 9 个 nature-* 对照 repo2 的 scientific-writing、unslop-academic-writing、venue-templates、abstract-and-title 等写作组。重叠面约占 repo1 技能量的一半。

各自独有：repo1 独有 CNKI、ScienceDirect、Web of Science 三个平台的站内全流程（浏览器自动化）、PDF 多路由下载与机构通道（scansci-pdf）、以及 Nature 专属深度写作包（专利、PPT、审稿、回复、中英对照精读）；repo2 独有 281 技能广度、免费 API 文献栈且脚本零依赖、PRISMA、BibTeX 工具链、引文幻觉基准、程序化 Zotero 集成、14 条 CI 安全与质量门禁、以及完整的许可与归属透明。

选哪个、为什么：选 repo2 为基座，repo1 作增量补充。理由：一、许可证与归属最清晰（整仓 MIT + 明确上游归属与 revision），可在本机无顾虑自由使用；二、核心技能实际是零依赖标准库脚本加免费公开 API，无浏览器、无付费凭证、无 MCP 前置，落地成本最低且可离线审阅；三、工程治理完备（白名单、扫描基线、CI 门禁、逐技能评测），维护活跃（2026 年 11 月 13 日仍有提交），符合「可长期依赖」的标准；四、从 repo1 只需取四个点——pm-search、nature-citation（以及按需的 nature-* 写作组纯提示词吸收），并明确回避 cnki-search、sd-search、wos-search 的浏览器反检测合规风险与 scansci-pdf 的灰色源与重依赖；五、若确有中文文献（CNKI）刚需，再单独评估 repo1 的 cnki-search。若只能选一个：repo2。

未验证项（按纪律如实列出）：一、未运行任何仓库代码，全部脚本行为结论来自静态阅读；二、chrome-devtools-mcp（npm 包）的许可证与行为未核实；三、CNKI、ScienceDirect、Web of Science 平台服务条款原文未获取，「违反 ToS」属风险提示而非结论；四、pybliometrics 配置文件在本机的具体位置未实测（代码只检查其存在性）；五、repo2 的 281 个技能中，与学术主线相关的约 40 个做了逐文件深读，其余为目录、frontmatter 与脚本清单级核实（全 281 项的一行速查表已落盘于 /tmp/re-audit/repo2-all-skills.txt，供复核）。