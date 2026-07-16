import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


# 当前文件：
# stage3_agent_harness/src/trace_logger.py
#
# parent        -> src
# parent.parent -> stage3_agent_harness
PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACE_DIR = PROJECT_DIR / "traces"

# 如果 traces 目录不存在，就自动创建
TRACE_DIR.mkdir(parents=True, exist_ok=True)


class TraceLogger:
    """
    Agent 运行轨迹记录器。

    每次创建 TraceLogger 对象时，
    默认生成一个独立的 JSONL 日志文件。
    """

    def __init__(self, trace_name: str | None = None):
        # 没有指定文件名时，自动生成唯一文件名
        if trace_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_id = uuid4().hex[:8]

            trace_name = (
                f"trace_{timestamp}_{short_id}.jsonl"
            )

        self.path = TRACE_DIR / trace_name
        self.step = 0

        # 创建一个新的空文件
        self.path.write_text("", encoding="utf-8")

    def log(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        向 JSONL 文件追加一条事件。

        event_type：
            事件名称，例如 run_started、tool_finished。

        data：
            与事件相关的具体数据。
        """

        self.step += 1

        record = {
            "step": self.step,
            "time": datetime.now().isoformat(
                timespec="seconds"
            ),
            "event_type": event_type,
            "data": data or {},
        }

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )