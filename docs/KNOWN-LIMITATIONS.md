# KNOWN-LIMITATIONS

已知局限与未完成事项。按「类别 / 内容 / 影响 / 缓解或出路」列出；凡未实测者明确标注。

## 一、能力边界

| 局限 | 影响 | 出路 |
|---|---|---|
| 无 JS 渲染抓取 | SPA、动态加载页面提取失败（如实标 EXTRACTION_FAILED） | 升级路径：Agent 浏览器工具（agent-browser/playwright-cli）；未内置渲染器是有意取舍（crawl4ai 过重） |
| CNKI 未安装 | 中文文献全文与知网题录缺失（基准 #10 全文 0/2） | 用户可选安装 SepineTam/cnki-mcp（步骤见 INSTALLATION-AND-CONFIGURATION.md，需机构权限） |
| Unpaywall 未启用 | 缺邮箱时 OA 解析与 pubmed MCP 全文链第三级不可用 | 设置环境变量 `RE_CONTACT_EMAIL` 即启用 |
| Semantic Scholar 共享池限流 | 偶发 429（基准中占供应商错误大头） | 引擎自动重试；可选 `S2_API_KEY` 提速；属于免费代价 |
| 引擎不做 LLM 调用 | 规划/扩展/综合的质量取决于 Agent；纯脚本调用时只有确定性能力 | 设计决策（脑在 Agent）；技能文档负责接缝 |
| 冲突检测为规则级 | 语义级矛盾（改写表述、隐式对立）检不到 | 规则候选 + Agent 复核；不声称全自动 |
| 词法相关性代理指标 | 基准中的相关性是词面匹配，不是人工判断 | 留作后续人工标注或 RACE 式评测（需付费模型） |

## 二、环境与工程

| 局限 | 影响 | 缓解 |
|---|---|---|
| 本机网关 DNS 间歇失联（openalex/crossref） | 无 DoH 时请求失败 | 引擎内置 DoH 兜底（已验证）；DoH 也失败属网络故障 |
| DNS rebinding 竞态窗口 | SSRF 防护存在理论时序窗口 | 单用户本地工具判定可接受；已在 fetcher 注释备案 |
| uv 可编辑安装 .pth 不稳定 | 曾两次导致入口失效 | 已弃用；双入口为 PYTHONPATH 包装脚本 |
| pubmed MCP 的 Unpaywall 抓取无大小上限 | 第三方已知 issue | 上游待修；调用该工具时留意 |
| SOCKS 代理告警（urllib3） | 噪声，无功能影响 | 来源未定位；不影响结果 |
| SearXNG 依赖单一容器 | 容器停了聚合降级 | 引擎自动降级其他供应商；`docker restart research-searxng` 恢复 |
| 磁盘余量约 12GB | 大量 PDF 全文会持续占用 | 文档都有 20MB 上限；research/papers 可定期清理（数据库保留元数据） |

## 三、基准与验证的未尽事项

- 未做多轮深研的增量收益测量（仅单轮对照）。
- 未对每家供应商做精确率抽样人工标注（当前只有词法代理与来源分类）。
- 基线延迟未记录（MCP 采集通道），只有引擎侧延迟分布。
- FACT 式主张级引用验证（某文献是否真的支持某主张）需逐篇阅读，本轮只做了存在性核验（6/6）；主张级留给实际研究会话按需执行。
- 基准#1 的基线查询词有微调（限流重试所致，已在数据文件注明）。

## 四、明确不做的（纪律性排除）

- 不绕访问控制：付费墙、登录墙、验证码、代理池一律不用；受限来源如实标状态。
- 不启用付费 API：Exa/Firecrawl/Parallel/Tavily/Scopus 等全部未接；不做静默计费。
- 不下载受限 PDF；CNKI 通道（若启用）只做检索与题录。
- 不把检索内容当指令；不做基于内容的自动外发动作。
- 不安装无许可证或停更风险组件（wong2/mcp-jina-reader、Mangofang/CNKICrawlerMCP、archora-skills 等）。
