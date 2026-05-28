# Nexus Bot

基于 Nanobot 运行时的多平台智能客服 Bot 工作区，支持飞书、Telegram、钉钉等平台，提供 FAQ 知识库查询、工单管理和基础客服记忆能力。

## 功能特性

- **FAQ 知识库**：覆盖通用问题、账户、计费、技术等常见问题，优先基于知识库回答
- **工单管理**：支持创建、查询、更新、列出工单，全程追踪处理进度
- **多平台接入**：预留 Telegram、飞书、钉钉渠道配置，提供一致的客服体验
- **记忆与升级策略**：支持记录长期有用的用户画像与高频问题，并在必要时升级人工处理
- **MCP 扩展能力**：通过本地 MCP Server 管理工单数据库

## 项目结构

```
nexus-bot/
├── config.json          # 主配置文件（模型、平台、MCP 等）
├── SOUL.md              # Bot 人格与回复规范
├── AGENTS.md            # Agent 能力定义与行为准则
├── USER.md              # 用户画像模板
├── HEARTBEAT.md         # 定时任务清单
├── MEMORY.md            # 记忆索引
├── knowledge/
│   └── faq/             # FAQ 知识库
│       ├── general.md
│       ├── account.md
│       ├── billing.md
│       └── technical.md
├── skills/
│   ├── faq/SKILL.md     # FAQ 查询技能
│   └── ticket/SKILL.md  # 工单管理技能
├── mcp_servers/
│   └── ticket_server.py # 工单 MCP Server
├── cron/                # 定时任务配置
├── sessions/            # 会话存储
└── data/                # 数据存储
```

## 仓库定位

这个仓库主要承载 `Nexus Bot` 的业务配置与知识资产，不包含 `Nanobot` 运行时本身。换句话说：

- `Nanobot` 负责提供 `agent` / `gateway` 等通用运行能力
- `nexus-bot` 负责提供客服人格、FAQ 知识库、Skill、记忆模板、MCP Server 和渠道配置

因此，启动本项目前需要先让本机具备可用的 `nanobot` CLI，但不一定非要把 `nanobot` 源码 clone 到当前目录。

## 快速开始

### 0. 前置条件

先准备好以下运行前提：

- 可用的 [Nanobot](https://github.com/HKUDS/nanobot) CLI
- `python3`
- Python 依赖安装能力（用于 MCP Server）

```bash
nanobot --help
python3 --version
```

如果本机还没有 `nanobot` 命令，再按照 Nanobot 项目的安装说明完成安装。关键点是最终 `nanobot` 命令可用。

### 1. 安装依赖

先安装本仓库用到的 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

### 2. 配置

复制环境变量模板，并填入实际值：

```bash
cp .env.example .env
```

需要重点配置：

- `NEXUS_API_KEY`
- `NEXUS_API_BASE`
- `TELEGRAM_BOT_TOKEN`（如果启用 Telegram）
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET`（如果启用飞书）
- `DINGTALK_APP_KEY` / `DINGTALK_APP_SECRET`（如果启用钉钉）

然后编辑 `config.json`，选择模型提供方并启用需要的平台。默认示例：

```json
{
  "agents": {
    "defaults": {
      "model": "YOUR_MODEL_NAME",
      "provider": "custom"
    }
  },
  "providers": {
    "custom": {
      "apiKey": "${NEXUS_API_KEY}",
      "apiBase": "${NEXUS_API_BASE}"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "${TELEGRAM_BOT_TOKEN}"
    }
  }
}
```

### 3. 启动

当 `nanobot` CLI 已可用后，只需编辑项目根目录下的 `config.json`，填入自己的 API Key 即可运行。

**cli：**

```bash
nanobot agent --config ./config.json
```

**多平台网关模式（Telegram / 飞书 / 钉钉）：**

```bash
nanobot gateway --config ./config.json
```

### 4. 验证

建议至少做以下 smoke test：

1. 启动 `agent` 模式，询问“这个机器人支持哪些平台？”
2. 再询问“帮我创建一个工单”，确认工单号能成功返回
3. 使用工单号继续查询一次状态

如果工单相关能力异常，优先检查：

- `python3` 是否可用
- `requirements.txt` 是否已安装
- `config.json` 中 `tools.mcpServers.ticket` 是否配置正确

### 5. 启用平台（可选）

在 `config.json` 的 `channels` 中启用需要的平台：

| 平台 | 配置项 | 状态 |
|------|--------|------|
| Telegram | `token` | 默认启用 |
| 飞书 | `appId` / `appSecret` | 需手动启用 |
| 钉钉 | `appKey` / `appSecret` | 需手动启用 |

### 6. 自定义知识库

编辑 `knowledge/faq/` 目录下的 Markdown 文件，添加或更新 FAQ 条目。

### 7. 自定义 Bot 行为

- **人格调整**：编辑 `SOUL.md` 修改语气、回复风格
- **流程与升级规则**：编辑 `AGENTS.md`
- **长期记忆模板**：编辑 `MEMORY.md` 与 `memory/MEMORY.md`
- **能力扩展**：在 `skills/` 下添加新的 Skill
- **定时任务**：在 `HEARTBEAT.md` 中添加周期性任务

## 工单状态流转

```
open → in_progress → pending_user → resolved → closed
```

## 许可证

MIT，详见 [LICENSE](/Users/seabo/Desktop/项目/nexus-bot/LICENSE)。
