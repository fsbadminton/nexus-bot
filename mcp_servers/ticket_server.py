"""
工单管理 MCP Server
提供工单的创建、查询、更新、关闭等功能，供 nanobot Agent 调用。
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

DB_PATH = Path(__file__).parent.parent / "data" / "tickets.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            user_id TEXT NOT NULL,
            platform TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


app = Server("ticket-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_ticket",
            description="创建新工单",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "问题标题"},
                    "description": {"type": "string", "description": "问题详细描述"},
                    "user_id": {"type": "string", "description": "用户 ID"},
                    "platform": {"type": "string", "description": "来源平台（feishu/telegram/dingtalk）"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "优先级",
                        "default": "medium",
                    },
                },
                "required": ["title", "description", "user_id"],
            },
        ),
        Tool(
            name="query_ticket",
            description="查询工单信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "工单号（精确查询）"},
                    "user_id": {"type": "string", "description": "用户 ID（查询该用户所有工单）"},
                },
            },
        ),
        Tool(
            name="update_ticket",
            description="更新工单状态或添加备注",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "工单号"},
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "pending_user", "resolved", "closed"],
                        "description": "新状态",
                    },
                    "note": {"type": "string", "description": "备注信息"},
                },
                "required": ["ticket_id"],
            },
        ),
        Tool(
            name="list_tickets",
            description="列出工单（可按状态筛选）",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "pending_user", "resolved", "closed"],
                        "description": "按状态筛选",
                    },
                    "limit": {"type": "integer", "description": "返回数量上限", "default": 20},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    conn = get_db()
    now = datetime.now().isoformat()

    try:
        if name == "create_ticket":
            ticket_id = f"TK-{uuid.uuid4().hex[:8].upper()}"
            conn.execute(
                """INSERT INTO tickets (id, title, description, user_id, platform, priority, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
                (ticket_id, arguments["title"], arguments.get("description", ""),
                 arguments["user_id"], arguments.get("platform", ""),
                 arguments.get("priority", "medium"), now, now),
            )
            conn.commit()
            result = {"ticket_id": ticket_id, "status": "open", "message": "工单创建成功"}

        elif name == "query_ticket":
            ticket_id = arguments.get("ticket_id")
            user_id = arguments.get("user_id")
            if ticket_id:
                row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
                result = dict(row) if row else {"error": f"未找到工单 {ticket_id}"}
            elif user_id:
                rows = conn.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
                result = [dict(r) for r in rows]
            else:
                result = {"error": "请提供 ticket_id 或 user_id"}

        elif name == "update_ticket":
            ticket_id = arguments["ticket_id"]
            updates = []
            params = []
            if "status" in arguments:
                updates.append("status = ?")
                params.append(arguments["status"])
            if "note" in arguments:
                updates.append("note = ?")
                params.append(arguments["note"])
            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(ticket_id)
                conn.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()
            row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
            result = dict(row) if row else {"error": f"未找到工单 {ticket_id}"}

        elif name == "list_tickets":
            limit = arguments.get("limit", 20)
            status = arguments.get("status")
            if status:
                rows = conn.execute("SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                                    (status, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?",
                                    (limit,)).fetchall()
            result = [dict(r) for r in rows]

        else:
            result = {"error": f"未知工具: {name}"}

    finally:
        conn.close()

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


if __name__ == "__main__":
    import asyncio

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(main())
