import json
from typing import Any

from src.permission import request_permission
from src.tool_registry import get_tool


def serialize_result(result: Any) -> str:
    """
    将工具返回值转换成可以发给模型的字符串。
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

    执行流程：
    1. 读取工具名称
    2. 解析工具参数
    3. 从注册表查找工具
    4. 检查是否属于危险工具
    5. 必要时请求用户授权
    6. 执行真正的 Python 函数
    """

    tool_name = tool_call.function.name
    raw_arguments = tool_call.function.arguments or "{}"

    # 模型返回的 arguments 是 JSON 字符串
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

    # 获取工具注册信息
    tool_info = get_tool(tool_name)

    dangerous = tool_info.get("dangerous", False)

    # 危险工具执行前请求权限
    if dangerous:
        allowed = request_permission(
            tool_name=tool_name,
            arguments=arguments,
        )

        if not allowed:
            denied_content = (
                f"工具 {tool_name} 未执行："
                "用户拒绝了本次操作授权。"
            )

            return {
                "status": "denied",
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "arguments": arguments,
                "result": None,
                "content": denied_content,
            }

    # 取出真正的 Python 函数
    tool_function = tool_info["function"]

    # 真正执行工具
    result = tool_function(**arguments)

    return {
        "status": "success",
        "tool_call_id": tool_call.id,
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
        "content": serialize_result(result),
    }