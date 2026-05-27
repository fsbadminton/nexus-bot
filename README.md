# Nexus Bot

基于 Nanobot 运行时的多平台智能客服 Bot 工作区，支持飞书、Telegram、钉钉等平台，提供 FAQ 知识库查询和工单管理服务。

## 功能特性

- **FAQ 知识库**：覆盖通用问题、账户、计费、技术等常见问题，自动匹配最佳答案
- **工单管理**：支持创建、查询、更新、关闭工单，全程追踪处理进度
- **多平台接入**：同时支持 Telegram、飞书、钉钉，提供一致的客服体验
- **智能对话**：温和专业的人格设定，自动处理常见问题，无法解决时转交人工

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

这个仓库主要承载的是 `Nexus Bot` 的业务配置与知识资产，不包含 `Nanobot` 运行时本身。换句话说：

- `Nanobot` 负责提供 `agent` / `gateway` 等通用运行能力
- `nexus-bot` 负责提供客服人格、FAQ 知识库、Skill、MCP Server 和渠道配置

因此，启动本项目前需要先让本机具备可用的 `nanobot` CLI，但不一定非要把 `nanobot` 源码 clone 到当前目录。

## 快速开始

### 0. 前置条件

先准备好可用的 [Nanobot](https://github.com/HKUDS/nanobot) CLI 运行时。

```bash
nanobot --help
```

如果本机还没有 `nanobot` 命令，再按照 Nanobot 项目的安装说明完成安装。你可以使用源码 clone、包管理器或任何其他官方支持的安装方式；关键点是最后 `nanobot` 命令已经可用。

### 1. 配置

编辑 `config.json`，填入以下信息：

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
      "apiKey": "YOUR_MIMO_API_KEY",
      "apiBase": "YOUR_API_BASE_URL"
    }
  },
  "channels": {
    "telegram": {
      "token": "YOUR_TELEGRAM_BOT_TOKEN"
    }
  }
}
```

### 2. 启动

当 `nanobot` CLI 已可用后，只需编辑项目根目录下的 `config.json`，填入自己的 API Key 即可运行。

**cli：**

```bash
nanobot agent --config ./config.json
```

**多平台网关模式（Telegram / 飞书 / 钉钉）：**

```bash
nanobot gateway --config ./config.json
```

### 3. 启用平台（可选）

在 `config.json` 的 `channels` 中启用需要的平台：

| 平台 | 配置项 | 状态 |
|------|--------|------|
| Telegram | `token` | 默认启用 |
| 飞书 | `appId` / `appSecret` | 需手动启用 |
| 钉钉 | `appKey` / `appSecret` | 需手动启用 |

### 4. 自定义知识库

编辑 `knowledge/faq/` 目录下的 Markdown 文件，添加或更新 FAQ 条目。

### 5. 自定义 Bot 行为

- **人格调整**：编辑 `SOUL.md` 修改语气、回复风格
- **能力扩展**：在 `skills/` 下添加新的 Skill
- **定时任务**：在 `HEARTBEAT.md` 中添加周期性任务

## 工单状态流转

```
open → in_progress → pending_user → resolved → closed
```

## 许可证

MIT
