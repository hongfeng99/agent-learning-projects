import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


# 当前文件位于：
# stage3_agent_harness/src/session_store.py
PROJECT_DIR = Path(__file__).resolve().parent.parent
SESSION_DIR = PROJECT_DIR / "sessions"

SESSION_DIR.mkdir(parents=True, exist_ok=True)


# session_id 只允许包含：
# 英文字母、数字、下划线和短横线
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def current_time() -> str:
    """
    返回当前时间字符串。
    """

    return datetime.now().isoformat(timespec="seconds")


class SessionStore:
    """
    保存和加载 Agent 会话。

    每个会话对应 sessions 目录中的一个 JSON 文件。
    """

    def __init__(
        self,
        session_id: str | None = None,
    ):
        # 没有传 session_id 时，自动生成一个新 ID
        if session_id is None:
            session_id = self.generate_session_id()

        self.validate_session_id(session_id)

        self.session_id = session_id
        self.path = SESSION_DIR / f"{session_id}.json"

        # 文件已经存在：加载旧会话
        if self.path.exists():
            self.data = self.load()

        # 文件不存在：创建新会话
        else:
            self.data = {
                "session_id": self.session_id,
                "created_at": current_time(),
                "updated_at": current_time(),
                "messages": [],
            }

            self.save()

    @staticmethod
    def generate_session_id() -> str:
        """
        自动生成唯一会话 ID。
        """

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        short_id = uuid4().hex[:8]

        return f"session_{timestamp}_{short_id}"

    @staticmethod
    def validate_session_id(session_id: str) -> None:
        """
        校验 session_id，避免非法路径。
        """

        if not SESSION_ID_PATTERN.fullmatch(session_id):
            raise ValueError(
                "session_id 只能包含英文字母、数字、"
                "下划线和短横线。"
            )

    @property
    def messages(self) -> list[dict[str, Any]]:
        """
        返回当前会话中的消息列表。
        """

        return self.data["messages"]

    @property
    def is_empty(self) -> bool:
        """
        判断当前会话是否还没有消息。
        """

        return len(self.messages) == 0

    def add_message(
        self,
        message: dict[str, Any],
    ) -> None:
        """
        添加一条消息，并立即保存。
        """

        if not isinstance(message, dict):
            raise TypeError("message 必须是字典")

        self.data["messages"].append(message)
        self.data["updated_at"] = current_time()

        self.save()

    def load(self) -> dict[str, Any]:
        """
        从 JSON 文件加载会话。
        """

        try:
            content = self.path.read_text(
                encoding="utf-8"
            )

            data = json.loads(content)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Session 文件不是有效 JSON：{self.path}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                "Session 文件顶层必须是 JSON 对象"
            )

        messages = data.get("messages")

        if not isinstance(messages, list):
            raise ValueError(
                "Session 文件中的 messages 必须是列表"
            )

        return data

    def save(self) -> None:
        """
        将当前会话写入 JSON 文件。
        """

        self.path.write_text(
            json.dumps(
                self.data,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )