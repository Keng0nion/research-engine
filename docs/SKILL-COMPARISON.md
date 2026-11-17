# SKILL-COMPARISON

四个候选技能库的对比与裁决。审计依据：源码级只读深查（2026 年 11 月 17 日），原始报告见 `docs/audit-raw/raw/`。

## 对比总表

| 维度 | KalarisLabs/research-agent-skills | YuanyuanMa03/academic-research-skills | Orchestra-Research/AI-Research-SKILLs | richard-kim-79/archora-skills |
|---|---|---|---|---|
| stars | 153 | 79 | 14589 | 50 |
| 技能规模 | 281 个 | 16 个 | 98 个 | 9 个 |
| 许可 | MIT（含上游归属与 revision 记录） | MIT | MIT | **无 LICENSE 文件** |
| 最近提交 | 2026-11-13（活跃） | 2026-10-29（活跃） | 2026-06（主分支） | 2026-05（停滞） |
| 定位 | 学术研究全生命周期 | 检索渠道 + Nature 写作 | ML 实验与训练引导 | 学术写作链 |
| 安全治理 | 最强（域名白名单、扫描基线、14 条 CI） | 常规 | 常规 | 无 |
| 依赖面 | 核心学术技能纯标准库 | 部分技能依赖浏览器/MCP | 纯提示词 | 纯提示词 |
| 与本项目相关性 | **高**（文献检索、引文、PRISMA、库覆盖） | **中高**（中文引文独有；平台抓取有合规风险） | 低（ML 训练而非检索） | 低且重复 |

## 裁决

**基座选 KalarisLabs/research-agent-skills**，理由：整仓 MIT 且归属透明（THIRD_PARTY_NOTICES 载明上游与 revision）；核心学术技能为零依赖标准库脚本加免费公开 API，落地成本最低；工程治理与安全基线为四者最高；维护最活跃。

**增量选 YuanyuanMa03/academic-research-skills 的 nature-citation**（GB/T 7714 中文引文导出，纯标准库）。

## 已安装技能清单（7 个，全部在 ~/.agents/skills/）

| 技能 | 来源 | 依赖 | 验证状态 |
|---|---|---|---|
| paper-lookup | KalarisLabs | 纯标准库 | 已配置（脚本审计通过） |
| citation-verification | KalarisLabs | 纯标准库 | 已配置（引擎内置同类能力双保险） |
| systematic-review-prisma | KalarisLabs | 纯标准库 | 已配置 |
| bibtex-hygiene | KalarisLabs | 零依赖 | 已配置 |
| reference-manager-interop | KalarisLabs | 零依赖 | 已配置 |
| database-lookup | KalarisLabs | 纯提示词（82 个数据库文档） | 已配置 |
| nature-citation | YuanyuanMa03 | 纯标准库（仅 api.crossref.org） | 已配置 |

来源与 revision 存证：`~/.agents/skills/RESEARCH-SKILLS-ORIGINS.md`（KalarisLabs @ e2c8aa0f，YuanyuanMa03 @ f4f4c18d）。

## 未安装的重点与理由

| 技能组 | 理由 |
|---|---|
| cnki-search / sd-search / wos-search（YuanyuanMa03） | 浏览器自动化依赖 + 反检测开关（`--disable-blink-features=AutomationControlled`），合规风险；CNKI 通道改用 SepineTam/cnki-mcp（用户可选、检索限定、本人登录） |
| scansci-pdf（YuanyuanMa03） | 桥接外部 MCP，默认全源竞速含灰色源；本项目只走合法开放获取路径 |
| nature-* 写作组 9 个纯提示词技能（YuanyuanMa03） | 与检索基础设施目标错位；纯提示词零成本，需要时可直接取用（已审计可用） |
| Orchestra 全库 | 核心为 ML 训练实验引导（vLLM、DeepSpeed 等），非检索；借鉴其 ara-rigor-reviewer 六维评审概念用于证据质量方法论。注：任务书点名的「AI research workflows」「Agent research」「Scientific evaluation」在该仓库并不存在（零命中），已在本档更正 |
| archora-skills | 无许可证文件 + 停滞 + 与 KalarisLabs 重复 |
| KalarisLabs 其余 270+ 技能 | 领域科学工具（rdkit、scanpy、qiskit 等）超出搜索引擎范围，按需可再取 |

## 任务书点名的技能存在性核实（关键修正）

- YuanyuanMa03：cnki-search / nature-academic-search / pm-search / sd-search / wos-search / scansci-pdf 全部存在；**gs-search 不存在**（作者于 v2.0.0 移除，README 残留安装命令）。
- KalarisLabs：paper-lookup / research-lookup / database-lookup / literature-review / systematic-review-prisma / citation-verification / scientific-critical-thinking **7 项全部存在**。
- Orchestra-Research：仅 `autoresearch` 与 RAG 分类真实；其余见上表说明。
