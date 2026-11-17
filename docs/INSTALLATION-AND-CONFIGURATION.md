# INSTALLATION-AND-CONFIGURATION

安装与配置的完整说明（2026 年 11 月 17 日实施）。所有路径为绝对路径，可直接复制执行复核。

## 一、目录总览

| 内容 | 位置 |
|---|---|
| 引擎项目根 | `/Users/luna/Documents/Dev/research-engine/` |
| 引擎 Python 环境 | `.venv/`（uv 管理，CPython 3.12.14） |
| 引擎入口（两个等价） | `bin/researchctl` 与 `.venv/bin/researchctl`（同为 PYTHONPATH 包装，不依赖可编辑安装） |
| 研究数据 | `research/research.db`；文档 `research/{papers,websites}`；报告 `research/reports` |
| SearXNG 部署文件 | `providers/searxng/`（compose 留档 + settings.yml） |
| 审计证据 | `docs/audit-raw/`（8 份原始报告） |
| 研究技能 | `~/.agents/skills/research-engine/`（源在项目 `skills/`） |
| 学术技能 | `~/.agents/skills/{paper-lookup, citation-verification, systematic-review-prisma, bibtex-hygiene, reference-manager-interop, database-lookup, nature-citation}` |
| MCP 配置 | `~/.zcode/cli/config.json` → `mcp.servers` |

## 二、SearXNG（本机回环）

实际部署命令（本机未装 docker compose，用等价 docker run）：

```bash
docker run -d --name research-searxng --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v /Users/luna/Documents/Dev/research-engine/providers/searxng/core-config:/etc/searxng:rw \
  -e SEARXNG_BASE_URL=http://127.0.0.1:8080/ \
  --cap-drop ALL --cap-add CHOWN --cap-add SETGID --cap-add SETUID \
  --log-driver json-file --log-opt max-size=1m --log-opt max-file=1 \
  docker.io/searxng/searxng:latest
```

关键配置（`core-config/settings.yml`）：`search.formats: [html, json]`（JSON API 必需）、`limiter: false`（单用户回环；开启需 valkey，compose 文件已留档）、`autocomplete: ""`（关闭对外前缀泄漏）、google 直连禁用（实测持续拒绝）、bing 启用。

复核：`curl -s 'http://127.0.0.1:8080/search?q=test&format=json' | head -c 200`
启停：`docker restart research-searxng` / `docker stop research-searxng`

## 三、MCP 服务器（~/.zcode/cli/config.json）

改动前的原始配置已备份为 `~/.zcode/cli/config.json.bak-20261117-researchengine`（回滚：复制回去并重启会话）。

新增条目（与既有 duckduckgo、blender 等并存）：

```json
"arxiv":   {"command": "uvx", "args": ["--from", "arxiv-mcp-server[pdf]", "arxiv-mcp-server",
             "--storage-path", "/Users/luna/Documents/Dev/research-engine/research/papers/arxiv"]},
"pubmed":  {"command": "npx", "args": ["-y", "@cyanheads/pubmed-mcp-server"]},
"mcpsurfr":{"command": "uvx", "args": ["mcpsurfr"]}
```

- 新服务器在 ZCode **下一次会话启动**时可用（本会话内已完成启动存活验证）。
- arxiv MCP 仅从 PyPI 安装（README 明示存在同名 npm 包供应链陷阱）。
- pubmed MCP 可选环境变量：`NCBI_API_KEY`（提速）、`NCBI_ADMIN_EMAIL`、`UNPAYWALL_EMAIL`（全文链第三级）；未设置时相应降级，不报错。

## 四、学术技能安装（已完成）

7 个技能从审计过的克隆复制到 `~/.agents/skills/`，来源与 revision 存证见该目录下 `RESEARCH-SKILLS-ORIGINS.md`（KalarisLabs @ e2c8aa0f，YuanyuanMa03 @ f4f4c18d）。
更新方法：重新克隆对应仓库到临时目录并覆制同名技能目录，同步更新存量文件中的 revision 行。

## 五、引擎环境

```bash
# 已创建；重建时执行：
cd /Users/luna/Documents/Dev/research-engine
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python trafilatura httpx pypdf
```

说明：`uv pip install -e .` 生成的 `_editable_impl .pth` 在本机时灵时不灵（两次失效），已弃用该机制；两个 researchctl 入口均为显式 PYTHONPATH 包装脚本，稳定可用。

## 六、可选配置

| 项 | 方法 | 作用 |
|---|---|---|
| Unpaywall 开放获取解析 | 环境变量 `RE_CONTACT_EMAIL=你的邮箱` | 启用全文回退链与 OA 解析（邮箱为 Unpaywall 强制要求） |
| Semantic Scholar 提速 | 环境变量 `S2_API_KEY` | 共享池 429 减少 |
| NCBI 提速 | 环境变量 `NCBI_API_KEY` | PubMed 3→10 请求/秒 |
| 引擎根目录覆盖 | 环境变量 `RE_ROOT` 或 `--root` | 数据目录搬迁 |
| CNKI 中文文献通道（可选，未安装） | 步骤见下 | 中文知网检索 |

### CNKI 通道启用步骤（用户自行决定）

前提：本人有机构 CNKI 访问权限。操作：`uv tool install` 或按仓库说明装 SepineTam/cnki-mcp（GPL-3.0，独立进程调用）→ 首次 `cnki-mcp login` 在可见浏览器中**本人完成机构认证**（凭据只存本机 profile）→ 在 `~/.zcode/cli/config.json` 增加对应 MCP 条目。
红线（写入技能纪律，启用后仍适用）：只做检索与题录；不使用任何全文下载功能；不破解验证码；不共享机构凭据；不超出其默认限速（1 请求/秒、每日 1000 次）。

## 七、健康复核清单（一次性五分钟）

```bash
/Users/luna/Documents/Dev/research-engine/bin/researchctl providers          # 期望：8 个 OK，unpaywall 视邮箱而定
curl -s 'http://127.0.0.1:8080/search?q=test&format=json' | head -c 120      # SearXNG JSON 正常
docker ps --filter name=research-searxng --format '{{.Status}}'              # 容器 Up
python3 -c "import json;print(len(json.load(open('/Users/luna/.zcode/cli/config.json'))['mcp']['servers']))"  # 7 个服务器
ls ~/.agents/skills | grep -cE "paper-lookup|citation-verification|systematic-review-prisma|bibtex-hygiene|reference-manager-interop|database-lookup|nature-citation|research-engine"  # 8
```
