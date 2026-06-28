import json
from datetime import datetime
from pathlib import Path


DEFAULT_MEMORY_PATH = Path("memory/memory.json")


def ensure_memory_file(memory_path: str | Path = DEFAULT_MEMORY_PATH) -> Path:
    """
    确保 memory.json 存在。
    如果不存在，就创建一个空的记忆文件。
    """
    path = Path(memory_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        data = {
            "facts": []
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    return path


def load_memories(memory_path: str | Path = DEFAULT_MEMORY_PATH) -> list[dict]:
    """
    读取所有记忆。
    """
    path = ensure_memory_file(memory_path)

    data = json.loads(path.read_text(encoding="utf-8"))

    return data.get("facts", [])


def save_memory(text: str, memory_path: str | Path = DEFAULT_MEMORY_PATH) -> dict:
    """
    保存一条新记忆。
    """
    path = ensure_memory_file(memory_path)

    data = json.loads(path.read_text(encoding="utf-8"))
    facts = data.get("facts", [])

    memory = {
        "id": len(facts) + 1,
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    facts.append(memory)
    data["facts"] = facts

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return memory


def format_memories(memories: list[dict]) -> str:
    """
    把记忆列表整理成给大模型看的文本。
    """
    if not memories:
        return "暂无记忆。"

    lines = []

    for memory in memories:
        lines.append(
            f"- [{memory['id']}] {memory['text']}，记录时间：{memory['created_at']}"
        )

    return "\n".join(lines)