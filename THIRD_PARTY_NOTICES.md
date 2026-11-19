# 第三方声明（THIRD_PARTY_NOTICES）

本仓库第一方代码适用 MIT（见 `LICENSE`）。以下第三方内容不适用本仓库许可证，各自许可证另行适用：

## 技能文件

第一方 Agent 技能已独立成仓 [Keng0nion/research-engine-skill](https://github.com/Keng0nion/research-engine-skill)（MIT），本仓库不再打包技能文件；学术技能（paper-lookup、citation-verification、systematic-review-prisma、bibtex-hygiene、reference-manager-interop、database-lookup、nature-citation）不在本仓库内打包，安装时从上游复制，来自：

- KalarisLabs/research-agent-skills（MIT），审计时 revision `e2c8aa0fba85f4f3e42c8cc329ec06c443d9af24`
- YuanyuanMa03/academic-research-skills（MIT），审计时 revision `f4f4c18d15918edfe3735bcec83d1f2e0e5bdba4`

详见 `docs/GITHUB-REPOSITORY-RESEARCH.md`。

## 运行时依赖的第三方服务/软件（不打包代码）

- SearXNG：AGPL-3.0。个人自托管无源码披露义务；修改后对外提供服务时，AGPL 第 13 条要求向用户提供对应源码。
- arxiv-mcp-server（Apache-2.0）、pubmed-mcp-server（Apache-2.0）、mcpsurfr（MIT）、mcp-duckduckgo：各自许可证见其仓库。
- Python 依赖（trafilatura、httpx、pypdf 等）：各自许可证见 PyPI。

## 审计过但未打包的项目

`docs/audit-raw/` 收录了 30+ 个候选仓库的审计报告。其中无许可证的项目（如 wong2/mcp-jina-reader、Mangofang/CNKICrawlerMCP、richard-kim-79/archora-skills）代码未被复用，仅作审计记录。
