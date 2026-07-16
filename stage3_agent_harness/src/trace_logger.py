import json
from datetime import datetime
from pathlib import Path


TRACE_DIR = Path("traces")
TRACE_DIR.mkdir(exist_ok=True)


class TraceLogger:
    def __init__(self, trace_name: str = "trace_demo.jsonl"):
        self.path = TRACE_DIR / trace_name
        self.step = 0

        # 每次新建 TraceLogger 时清空旧 trace，避免多次运行结果混在一起
        self.path.write_text("", encoding="utf-8")

    def log(self, event_type: str, data: dict):
        self.step += 1

        record = {
            "step": self.step,
            "time": datetime.now().isoformat(timespec="seconds"),
            "event_type": event_type,
            "data": data,
        }

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")