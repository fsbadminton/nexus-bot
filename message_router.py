#!/usr/bin/env python3
"""
Normalize raw platform message payloads into a unified message object.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Platform(str, Enum):
    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    TELEGRAM = "telegram"
    QQ = "qq"


@dataclass
class UnifiedMessage:
    message_id: str
    platform: Platform
    user_id: str
    user_name: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: str | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)

    def to_prompt(self) -> str:
        lines = [
            f"[source: {self.platform.value}]",
            f"[user: {self.user_name}({self.user_id})]",
            f"[message_id: {self.message_id}]",
            f"[time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]",
        ]
        if self.reply_to:
            lines.append(f"[reply_to: {self.reply_to}]")
        if self.attachments:
            lines.append(f"[attachments: {len(self.attachments)}]")
        lines.append("")
        lines.append(f"user_message: {self.content}")
        return " ".join(lines[:4]) + ("\n" + "\n".join(lines[4:]) if len(lines) > 4 else "")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["platform"] = self.platform.value
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


class MessageRouter:
    @classmethod
    def route(cls, platform: str | Platform, payload: dict[str, Any]) -> UnifiedMessage | None:
        platform_value = Platform(platform)
        if platform_value == Platform.FEISHU:
            return cls.from_feishu(payload)
        if platform_value == Platform.DINGTALK:
            return cls.from_dingtalk(payload)
        if platform_value == Platform.TELEGRAM:
            return cls.from_telegram(payload)
        if platform_value == Platform.QQ:
            return cls.from_qq(payload)
        raise ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    def from_feishu(payload: dict[str, Any]) -> UnifiedMessage | None:
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
        sender_name = sender.get("sender_name") or sender.get("name") or str(sender_id)

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
    def from_qq(payload: dict[str, Any]) -> UnifiedMessage | None:
        event_type = payload.get("t")
        message = payload.get("d") if isinstance(payload.get("d"), dict) else payload
        if not isinstance(message, dict):
            return None

        if not event_type:
            event_type = MessageRouter._detect_qq_event_type(message)
        if event_type not in {
            "AT_MESSAGE_CREATE",
            "DIRECT_MESSAGE_CREATE",
            "MESSAGE_CREATE",
            "GROUP_AT_MESSAGE_CREATE",
            "C2C_MESSAGE_CREATE",
        }:
            return None

        text = str(message.get("content", "")).strip()
        if not text:
            return None

        author = message.get("author", {})
        if not isinstance(author, dict):
            author = {}

        user_id = MessageRouter._qq_user_id(event_type, author)
        user_name = MessageRouter._qq_user_name(author, user_id)

        return UnifiedMessage(
            message_id=str(message.get("id", "")),
            platform=Platform.QQ,
            user_id=user_id,
            user_name=user_name,
            content=text,
            timestamp=MessageRouter._parse_timestamp(message.get("timestamp")),
            reply_to=MessageRouter._qq_reply_to(message),
            attachments=MessageRouter._extract_qq_attachments(message),
        )

    @staticmethod
    def _safe_json_loads(raw: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
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
        reply_to = message.get("reply_to_message", {})
        if not reply_to:
            return None
        reply_message_id = reply_to.get("message_id")
        return str(reply_message_id) if reply_message_id is not None else None

    @staticmethod
    def _detect_qq_event_type(message: dict[str, Any]) -> str | None:
        author = message.get("author", {})
        if not isinstance(author, dict):
            return None

        if "user_openid" in author:
            return "C2C_MESSAGE_CREATE"
        if "group_openid" in message and "member_openid" in author:
            return "GROUP_AT_MESSAGE_CREATE"
        if "guild_id" in message and "channel_id" in message:
            if "src_guild_id" in message:
                return "DIRECT_MESSAGE_CREATE"
            return "AT_MESSAGE_CREATE"
        return None

    @staticmethod
    def _qq_user_id(event_type: str, author: dict[str, Any]) -> str:
        if event_type == "C2C_MESSAGE_CREATE":
            value = author.get("user_openid")
        elif event_type == "GROUP_AT_MESSAGE_CREATE":
            value = author.get("member_openid")
        else:
            value = author.get("id")
        return str(value or "unknown")

    @staticmethod
    def _qq_user_name(author: dict[str, Any], user_id: str) -> str:
        value = author.get("username")
        return str(value or user_id)

    @staticmethod
    def _qq_reply_to(message: dict[str, Any]) -> str | None:
        reference = message.get("message_reference", {})
        if not isinstance(reference, dict):
            return None
        value = reference.get("message_id")
        return str(value) if value else None

    @staticmethod
    def _extract_qq_attachments(message: dict[str, Any]) -> list[dict[str, Any]]:
        attachments = message.get("attachments", [])
        if not isinstance(attachments, list):
            return []

        result: list[dict[str, Any]] = []
        for item in attachments:
            if not isinstance(item, dict):
                continue

            attachment: dict[str, Any] = {}
            for key in (
                "content_type",
                "filename",
                "height",
                "width",
                "size",
                "url",
                "voice_wav_url",
                "asr_refer_text",
            ):
                if key in item:
                    attachment[key] = item[key]

            if attachment:
                result.append(attachment)

        return result


def route_message(platform: str | Platform, payload: dict[str, Any]) -> UnifiedMessage | None:
    return MessageRouter.route(platform, payload)
