from src.tools.file_tools import list_files, read_file, write_file, summarize_file


TOOL_REGISTRY = {
    "list_files": {
        "function": list_files,
        "description": "列出 demo_workspace 中的文件",
        "dangerous": False,
    },
    "read_file": {
        "function": read_file,
        "description": "读取 demo_workspace 中的指定文件",
        "dangerous": False,
    },
    "write_file": {
        "function": write_file,
        "description": "写入 demo_workspace 中的指定文件",
        "dangerous": True,
    },
    "summarize_file": {
        "function": summarize_file,
        "description": "读取文件并生成简短总结",
        "dangerous": False,
    },
}


def get_tool(name: str):
    if name not in TOOL_REGISTRY:
        raise ValueError(f"未知工具: {name}")

    return TOOL_REGISTRY[name]


def list_tool_descriptions() -> str:
    lines = []

    for name, info in TOOL_REGISTRY.items():
        dangerous = "危险工具，需要确认" if info["dangerous"] else "安全工具"
        lines.append(f"- {name}: {info['description']} [{dangerous}]")

    return "\n".join(lines)