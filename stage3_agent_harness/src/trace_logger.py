import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


# trace_logger.py 位于：
# stage3_agent_harness/src/trace_logger.py
#
# parent        -> src
# parent.parent -> stage3_agent_harness
PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACE_DIR = PROJECT_DIR / "traces"

TRACE_DIR.mkdir(parents=True, exist_ok=True)


class TraceLogger:
    """
    Agent 运行轨迹记录器。

    每次创建 TraceLogger 时，都会生成一个独立的 JSONL 文件。
    JSONL 的特点是：每一行都是一个完整 JSON 对象。
    """

    def __init__(self, trace_name: str | None = None):
        if trace_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_id = uuid4().hex[:8]

            trace_name = (
                f"trace_{timestamp}_{short_id}.jsonl"
            )

        self.path = TRACE_DIR / trace_name
        self.step = 0

        # 创建空 trace 文件
        self.path.write_text("", encoding="utf-8")

    def log(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        向 trace 文件追加一条事件记录。
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