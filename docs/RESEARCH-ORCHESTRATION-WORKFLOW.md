# RESEARCH-ORCHESTRATION-WORKFLOW

研究工作流规范：四种模式、九步标准流程、停止规则与输出规范。Agent 按本档执行；命令速查见技能 `~/.agents/skills/research-engine/SKILL.md`（技能源：[Keng0nion/research-engine-skill](https://github.com/Keng0nion/research-engine-skill)）。

## 模式选择规则

| 模式 | 触发条件 | 预算 | 交付 |
|---|---|---|---|
| quick | 单点事实、快速核对 | 1 至 2 次检索、不建会话 | 直接回答 + 来源链接 |
| standard | 需要对比或可靠来源 | 2 至 4 次检索、3 至 5 篇获取、会话 | 带引用的答案或短报告 |
| deep | 复杂问题、多角度、有争议 | 最多 3 轮、每轮多供应商、证据卡 ≥ 5 | 结构化报告（含冲突与空白） |
| systematic | 学术综述、可复现要求 | 严格记录检索式与日期、PRISMA | PRISMA 流程 + 证据表 + 全参考文献 |

选择权在 Agent；用户显式指定模式时从其指定。模式间可升级（quick 发现深度不够转 standard/deep），不降级静默。

## 标准流程（九步）

1. **立案**：`session new "<问题原文>" --mode <模式>`（quick 跳过）。
2. **规划**：Agent 写出目标、子问题、中英关键词、同义词、技术术语、域名限定词、来源矩阵，`session update --plan` 落库。
3. **检索第一轮**：`search --session <sid> --expand`；`--domain auto` 自动路由（bio/cs/zh/news 等），必要时显式覆盖；中文专题另跑 `--domain zh`。
4. **获取**：`session show` 看文档池；核心文档 `fetch --docs 1,2,3`；访问状态如实记录（全文/仅摘要/受限/失败）。
5. **证据卡**：`evidence draft --session --doc` 生成草稿；Agent 阅读全文或摘要后 `evidence update` 填写主张、方法、数据集、数字、局限与四维评级。
6. **引文情报**：对有 DOI/arXiv 的文档 `citations build`；核验关键引文 `citations verify --doi/--title`；核验结果回填证据卡 `citation_status`。
7. **冲突检测与复核**：`conflicts detect --save`；Agent 逐条复核（解释差异原因或标记未解决），`conflicts update` 记录状态；不取多数意见。
8. **迭代轮**：核对缺口（未答子问题、欠覆盖平台、缺失一手来源）→ 生成新查询词 → `session update --bump-round` + `search --round N` → 回到第 4 步。
9. **综合报告**：`report --session` 生成骨架 → Agent 填写「重要发现 / 学术发现 / 空白与局限」→ 报告落在 `research/reports/<sid>.md`。

## 停止规则（MODULE 9）

满足任一即停：全部关键子问题有证据支撑；新一轮新增来源显著下降（参考阈值：新文档占比低于 15%）；已达轮数上限（默认 3，用户可调）；用户叫停。
禁止无限递归研究；每轮结束必须留下轮次结论（可解释为什么继续或停止）。

## 任务分配规则（并行执行）

- 引擎线程池默认 6；单供应商超时 25 秒；文档获取超时 40 秒。
- 单供应商失败不拖垮整轮（错误入 `queries` 表与报告）；限频 429 等 3 秒重试；连续失败按缺口上报。
- 不为凑数创建无止境 worker；预算数字全部来自 `config/engine.yaml`。

## 输出规范

- 引用一律带来源（`[doc_id]` 或 URL）；报告参考文献列出访问状态与检索时间。
- 区分「已证实事实 / 假设 / 解读」；冲突证据保留双方。
- 访问受限的文献必须标注「仅摘要/受限」，不得以全读口吻引用。
- 语言：跟随用户问题语言；术语保留英文原词。

## 四模式的验收标准

| 模式 | 验收 |
|---|---|
| quick | 回答正确性 + 至少 1 个可验证来源 |
| standard | 引用可点击复现；来源 ≥ 3；对比类问题需交叉来源 |
| deep | 证据卡 ≥ 5 且四维评级完整；冲突段有处理记录；轮次记录完整 |
| systematic | 检索式、日期、数据库清单可复现；去重记录；PRISMA 数字自洽；引文核验通过率记录 |
