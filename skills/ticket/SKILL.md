---
name: ticket
description: 工单管理 - 创建、查询、更新、关闭工单
metadata:
  nanobot:
    always: true
---

# 工单管理

当用户需要创建工单或查询工单状态时使用此 skill。

## 功能

- **创建工单**：记录用户问题，生成工单号
- **查询工单**：根据工单号查询状态和处理进度
- **更新工单**：添加备注、变更状态
- **关闭工单**：问题解决后关闭工单

## 工单状态

- `open` - 待处理
- `in_progress` - 处理中
- `pending_user` - 等待用户回复
- `resolved` - 已解决
- `closed` - 已关闭

## 使用方式

通过 MCP Server (`mcp_servers/ticket_server.py`) 操作工单数据库。

### 创建工单
调用 MCP 工具 `create_ticket`，传入：
- `title`: 问题标题
- `description`: 问题描述
- `user_id`: 用户 ID
- `platform`: 来源平台
- `priority`: 优先级 (low/medium/high/urgent)

### 查询工单
调用 MCP 工具 `query_ticket`，传入：
- `ticket_id`: 工单号（精确查询）
- `user_id`: 用户 ID（查询该用户所有工单）

### 更新工单
调用 MCP 工具 `update_ticket`，传入：
- `ticket_id`: 工单号
- `status`: 新状态
- `note`: 备注信息

## 话术

- 创建成功："已为您创建工单 #{ticket_id}，我们会尽快处理。您可以通过工单号随时查询进度。"
- 查询结果："工单 #{ticket_id} 当前状态：{status}。{note}"
- 未找到："未找到工单 #{ticket_id}，请确认工单号是否正确。"
