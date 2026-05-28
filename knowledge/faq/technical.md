# 技术问题

## Q: 这个 Nexus Bot 怎么启动？
A: 当前仓库是基于 Nanobot 运行时的客服工作区。准备好可用的 `nanobot` CLI、安装 `requirements.txt` 里的 Python 依赖、完成 `config.json` 和环境变量配置后，即可使用 `nanobot agent --config ./config.json` 或 `nanobot gateway --config ./config.json` 启动。

## Q: 工单功能依赖什么？
A: 工单功能由 `mcp_servers/ticket_server.py` 提供，通过 MCP Server 访问本地 SQLite 数据库 `data/tickets.db`。运行前需要确保 `python3` 可用，并安装 `mcp` 依赖。

## Q: 为什么机器人没有回答我的问题？
A: 常见原因包括：1) 知识库中没有对应条目；2) 渠道配置未启用；3) 模型或 API 配置不正确；4) MCP 服务未成功启动。遇到这种情况，建议先检查 `config.json`、环境变量和依赖安装情况。

## Q: 如何扩展知识库？
A: 直接编辑 `knowledge/faq/` 下的 Markdown 文件即可。新增条目时，建议使用稳定、可验证的信息，并尽量覆盖用户真实高频问题。

## Q: 如何查看工单状态？
A: 您可以提供工单号，由机器人调用工单查询能力返回当前状态；如果您是维护者，也可以通过 MCP 工具直接查询数据库记录。
