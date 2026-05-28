---
name: ticket
description: 工单管理 - 创建、查询、更新、关闭工单
metadata:
  nanobot:
    always: true
---

# 工单管理技能

## 描述

通过 MCP Server `ticket` 创建、查询、更新和列出工单，用于承接 FAQ 未覆盖、故障排查、投诉升级和人工跟进场景。

## 适用场景

- 用户主动要求人工处理
- 知识库未命中或答案不够准确
- 出现故障、投诉、紧急问题、数据异常
- 用户想查询已有工单进度

## 可用工具

### `create_ticket`

用于创建新工单。

参数：
- `title`：工单标题
- `description`：问题详细描述
- `user_id`：用户 ID
- `platform`：来源平台
- `priority`：优先级，支持 `low` / `medium` / `high` / `urgent`

### `query_ticket`

用于按工单号或用户 ID 查询工单。

参数：
- `ticket_id`：精确查询单张工单
- `user_id`：查询该用户相关工单

### `update_ticket`

用于更新状态或补充备注。

参数：
- `ticket_id`：工单号
- `status`：`open` / `in_progress` / `pending_user` / `resolved` / `closed`
- `note`：补充说明

### `list_tickets`

用于列出工单，可按状态筛选。

参数：
- `status`：可选状态筛选
- `limit`：返回数量上限

## 工单处理策略

- 一般咨询升级：`medium`
- 影响使用但有替代方案：`high`
- 服务不可用、支付争议、投诉升级：`urgent`

## 回复模板

创建成功：

```text
已为您创建工单 {ticket_id}，当前状态是 open。我们会尽快跟进，您也可以随时把工单号发给我查询进度。
```

查询结果：

```text
工单 {ticket_id} 当前状态为 {status}。如有最新进展，我也可以继续帮您同步。
```

未找到：

```text
抱歉，我暂未查到这个工单号。请您确认工单号是否正确，或告诉我您的用户信息，我帮您继续查。
```

## 注意事项

- 工单描述要保留用户原始问题关键信息
- 不要把密码、验证码、银行卡等敏感信息写进工单
- 如果已经建单，回复里必须明确给出工单号
