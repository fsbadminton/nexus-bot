#!/usr/bin/env python3
"""
message_router.py - 多平台消息统一路由模块

这个模块不直接接管 Nanobot 的 channel 运行时，而是提供一层
"平台原始消息 -> 统一消息语义对象" 的标准化能力，方便后续：

1. 为不同平台消息补齐统一上下文
2. 在进入 FAQ / 工单逻辑前做一致的预处理
3. 将统一结构转换成适合发送给 Nanobot 的 prompt
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Platform(str, Enum):
    """支持的平台枚举。"""

    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    TELEGRAM = "telegram"


@dataclass
class UnifiedMessage:
    """统一消息格式，用于抹平多平台消息结构差异。"""

    message_id: str
    platform: Platform
    user_id: str
    user_name: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: str | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)

    def to_prompt(self) -> str:
        """转换为更适合交给 Nanobot 的标准化 prompt。"""
        lines = [
            f"[来源: {self.platform.value}]",
            f"[用户: {self.user_name}({self.user_id})]",
            f"[消息ID: {self.message_id}]",
            f"[时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]",
        ]
        if self.reply_to:
            lines.append(f"[回复消息: {self.reply_to}]")
        if self.attachments:
            lines.append(f"[附件数: {len(self.attachments)}]")
        lines.append("")
        lines.append(f"用户提问: {self.content}")
        return " ".join(lines[:4]) + ("\n" + "\n".join(lines[4:]) if len(lines) > 4 else "")

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化字典。"""
        payload = asdict(self)
        payload["platform"] = self.platform.value
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


class MessageRouter:
    """多平台消息标准化路由器。"""

    @classmethod
    def route(cls, platform: str | Platform, payload: dict[str, Any]) -> UnifiedMessage | None:
        """将指定平台的原始 payload 转为统一消息对象。"""
        platform_value = Platform(platform)
        if platform_value == Platform.FEISHU:
            return cls.from_feishu(payload)
        if platform_value == Platform.DINGTALK:
            return cls.from_dingtalk(payload)
        if platform_value == Platform.TELEGRAM:
            return cls.from_telegram(payload)
        raise ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    def from_feishu(payload: dict[str, Any]) -> UnifiedMessage | None:
        """
        解析飞书 webhook 消息。

        兼容：
        - URL 验证请求
        - 文本消息
        - 带 message.content JSON 字符串的结构
        """
        if payload.get("type") == "url_verification":
            return None

        event = payload.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})

        content_payload = MessageRouter._safe_json_loads(message.get("content", "{}"))
        text = str(content_payload.get("text", "")).strip()
        if not text:
            return None

        sender_id = (
            sender.get("sender_id", {}).get("user_id")
            or sender.get("sender_id", {}).get("open_id")
            or "unknown"
        )
        sender_name = (
            sender.get("sender_name")
            or sender.get("name")
            or str(sender_id)
        )

        return UnifiedMessage(
            message_id=str(message.get("message_id", "")),
            platform=Platform.FEISHU,
            user_id=str(sender_id),
            user_name=str(sender_name),
            content=text,
            timestamp=MessageRouter._parse_timestamp(
                message.get("create_time") or event.get("create_time")
            ),
            reply_to=message.get("parent_id") or message.get("root_id"),
            attachments=MessageRouter._extract_feishu_attachments(content_payload, message),
        )

    @staticmethod
    def from_dingtalk(payload: dict[str, Any]) -> UnifiedMessage | None:
        """解析钉钉 webhook 消息。"""
        text = str(payload.get("text", {}).get("content", "")).strip()
        if not text:
            return None

        sender_id = payload.get("senderStaffId") or payload.get("senderId") or "unknown"
        sender_name = payload.get("senderNick") or payload.get("senderStaffId") or str(sender_id)

        attachments = []
        if payload.get("msgtype") and payload.get("msgtype") != "text":
            attachments.append(
                {
                    "type": payload.get("msgtype"),
                    "raw": payload,
                }
            )

        return UnifiedMessage(
            message_id=str(payload.get("msgId") or payload.get("messageId") or ""),
            platform=Platform.DINGTALK,
            user_id=str(sender_id),
            user_name=str(sender_name),
            content=text,
            timestamp=MessageRouter._parse_timestamp(payload.get("createAt") or payload.get("timestamp")),
            reply_to=payload.get("conversationId"),
            attachments=attachments,
        )

    @staticmethod
    def from_telegram(payload: dict[str, Any]) -> UnifiedMessage | None:
        """解析 Telegram webhook/update 消息。"""
        message = payload.get("message") or payload.get("edited_message") or {}
        text = str(message.get("text") or message.get("caption") or "").strip()
        if not text:
            return None

        user = message.get("from", {})
        chat = message.get("chat", {})
        user_id = user.get("id", "unknown")
        user_name = (
            user.get("username")
            or " ".join(part for part in [user.get("first_name"), user.get("last_name")] if part)
            or chat.get("title")
            or str(user_id)
        )

        return UnifiedMessage(
            message_id=str(message.get("message_id", "")),
            platform=Platform.TELEGRAM,
            user_id=str(user_id),
            user_name=str(user_name),
            content=text,
            timestamp=MessageRouter._parse_timestamp(message.get("date")),
            reply_to=MessageRouter._telegram_reply_to(message),
            attachments=MessageRouter._extract_telegram_attachments(message),
        )

    @staticmethod
    def _safe_json_loads(raw: str) -> dict[str, Any]:
        """安全解析 JSON 字符串。"""
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """
        解析不同平台的时间字段。

        支持：
        - Unix 秒
        - Unix 毫秒
        - ISO 字符串
        - 缺失时回退为 now
        """
        if value in (None, ""):
            return datetime.now()

        if isinstance(value, (int, float)):
            numeric = float(value)
            if numeric > 1_000_000_000_000:
                numeric = numeric / 1000.0
            return datetime.fromtimestamp(numeric)

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return datetime.now()
            if raw.isdigit():
                return MessageRouter._parse_timestamp(int(raw))
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now()

        return datetime.now()

    @staticmethod
    def _extract_feishu_attachments(
        content_payload: dict[str, Any], message: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """提取飞书附件信息。"""
        attachments: list[dict[str, Any]] = []
        for key in ("image_key", "file_key", "media_key"):
            if key in content_payload:
                attachments.append({"type": key, "value": content_payload[key]})
        if message.get("message_type") and message.get("message_type") != "text":
            attachments.append(
                {
                    "type": message.get("message_type"),
                    "raw": content_payload or message,
                }
            )
        return attachments

    @staticmethod
    def _extract_telegram_attachments(message: dict[str, Any]) -> list[dict[str, Any]]:
        """提取 Telegram 附件信息。"""
        attachments: list[dict[str, Any]] = []
        for key in ("photo", "document", "audio", "voice", "video", "animation", "location"):
            if key not in message:
                continue
            value = message[key]
            if key == "photo" and isinstance(value, list):
                attachments.append({"type": "photo", "count": len(value)})
            else:
                attachments.append({"type": key, "raw": value})
        return attachments

    @staticmethod
    def _telegram_reply_to(message: dict[str, Any]) -> str | None:
        """提取 Telegram 被回复消息 ID。"""
        reply_to = message.get("reply_to_message", {})
        if not reply_to:
            return None
        reply_message_id = reply_to.get("message_id")
        return str(reply_message_id) if reply_message_id is not None else None


def route_message(platform: str | Platform, payload: dict[str, Any]) -> UnifiedMessage | None:
    """函数式入口，便于在脚本或后续 webhook 层直接调用。"""
    return MessageRouter.route(platform, payload)

