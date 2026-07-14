import json
from datetime import datetime
from pathlib import Path


SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)


class SessionStore:
    def __init__(self, session_name: str = "session_demo.json"):
        self.path = SESSION_DIR / session_name
        self.data = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "messages": [],
        }

    def add_message(self, role: str, content: str):
        self.data["messages"].append({
            "role": role,
            "content": content,
        })
        self.data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.save()

    def save(self):
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )