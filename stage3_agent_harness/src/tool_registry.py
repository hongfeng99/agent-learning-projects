from src.tools.file_tools import (
    list_files,
    read_file,
    write_file,
    summarize_file,
)


TOOL_REGISTRY = {
    "list_files": {
        "function": list_files,
        "description": "列出 demo_workspace 工作区中的所有文件",
        "dangerous": False,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    "read_file": {
        "function": read_file,
        "description": "读取 demo_workspace 工作区中的指定文本文件",
        "dangerous": False,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "需要读取的文件名，例如 note.txt",
                }
            },
            "required": ["filename"],
        },
    },

    "write_file": {
        "function": write_file,
        "description": "向 demo_workspace 工作区中的指定文件写入内容",
        "dangerous": True,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "需要写入的文件名，例如 summary.txt",
                },
                "content": {
                    "type": "string",
                    "description": "需要写入文件的文本内容",
                },
            },
            "required": ["filename", "content"],
        },
    },

    "summarize_file": {
        "function": summarize_file,
        "description": "读取并简单总结工作区中的指定文本文件",
        "dangerous": False,
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "需要总结的文件名，例如 note.txt",
                }
            },
            "required": ["filename"],
        },
    },
}


def get_tool(tool_name: str) -> dict:
    """
    根据工具名称获取工具的完整注册信息。
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"未知工具：{tool_name}")

    return TOOL_REGISTRY[tool_name]


def get_tool_schemas() -> list[dict]:
    """
    将 Python 内部的工具注册表，
    转换成大模型 function calling 所需要的 tools 格式。

    注意：
    function 和 dangerous 是 Harness 内部使用的信息，
    不需要直接发送给大模型。
    """

    schemas = []

    for tool_name, tool_info in TOOL_REGISTRY.items():
        schema = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_info["description"],
                "parameters": tool_info["parameters"],
            },
        }

        schemas.append(schema)

    return schemas