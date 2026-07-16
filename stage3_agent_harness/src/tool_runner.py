import json
from typing import Any

from src.tool_registry import get_tool


def serialize_result(result: Any) -> str:
    """
    将工具执行结果转换为字符串。

    后续把工具结果返回给模型时，
    tool message 的 content 必须是字符串。
    """

    if isinstance(result, str):
        return result

    return json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    )


def execute_tool_call(tool_call) -> dict:
    """
    执行模型产生的一次工具调用。

    参数 tool_call 是模型返回的工具调用对象，例如：

    ChatCompletionMessageFunctionToolCall(
        id="call_xxx",
        function=Function(
            name="list_files",
            arguments="{}"
        )
    )
    """

    tool_name = tool_call.function.name
    raw_arguments = tool_call.function.arguments

    # 模型返回的 arguments 是 JSON 字符串，
    # 需要转换成 Python 字典
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"工具 {tool_name} 的参数不是有效 JSON："
            f"{raw_arguments}"
        ) from error

    if not isinstance(arguments, dict):
        raise ValueError(
            f"工具 {tool_name} 的参数必须是 JSON 对象"
        )

    # 从 Tool Registry 中查找工具信息
    tool_info = get_tool(tool_name)

    # 取出真正的 Python 函数对象
    tool_function = tool_info["function"]

    # 使用 **arguments 将字典参数传入函数
    result = tool_function(**arguments)

    return {
        "tool_call_id": tool_call.id,
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
        "content": serialize_result(result),
    }