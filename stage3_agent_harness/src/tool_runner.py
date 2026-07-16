import json
from typing import Any

from src.permission import request_permission
from src.tool_registry import get_tool
from src.trace_logger import TraceLogger


def serialize_result(result: Any) -> str:
    """
    将工具返回值转换成字符串。

    因为发送给模型的 tool message，
    content 应当是字符串。
    """

    if isinstance(result, str):
        return result

    return json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def execute_tool_call(
    tool_call,
    trace: TraceLogger | None = None,
) -> dict:
    """
    执行一次模型产生的工具调用。

    trace 是可选参数：
    - 传入 TraceLogger：记录日志
    - 不传入：仍可正常执行工具
    """

    tool_name = tool_call.function.name
    raw_arguments = (
        tool_call.function.arguments or "{}"
    )

    # 记录：模型请求了什么工具
    if trace:
        trace.log(
            "tool_requested",
            {
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "raw_arguments": raw_arguments,
            },
        )

    # 模型返回的参数是 JSON 字符串
    try:
        arguments = json.loads(raw_arguments)

    except json.JSONDecodeError as error:
        if trace:
            trace.log(
                "tool_failed",
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )

        raise ValueError(
            f"工具 {tool_name} 的参数不是有效 JSON："
            f"{raw_arguments}"
        ) from error

    if not isinstance(arguments, dict):
        error_message = (
            f"工具 {tool_name} 的参数必须是 JSON 对象"
        )

        if trace:
            trace.log(
                "tool_failed",
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "error_type": "InvalidArguments",
                    "error": error_message,
                },
            )

        raise ValueError(error_message)

    # 从注册表中找到工具
    try:
        tool_info = get_tool(tool_name)

    except Exception as error:
        if trace:
            trace.log(
                "tool_failed",
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )

        raise

    dangerous = tool_info.get("dangerous", False)

    # 危险工具需要用户授权
    if dangerous:
        allowed = request_permission(
            tool_name=tool_name,
            arguments=arguments,
        )

        if trace:
            trace.log(
                "permission_checked",
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "allowed": allowed,
                },
            )

        # 用户拒绝
        if not allowed:
            denied_content = (
                f"工具 {tool_name} 未执行："
                "用户拒绝了本次操作授权。"
            )

            if trace:
                trace.log(
                    "tool_denied",
                    {
                        "tool_call_id": tool_call.id,
                        "tool_name": tool_name,
                        "arguments": arguments,
                    },
                )

            return {
                "status": "denied",
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "arguments": arguments,
                "result": None,
                "content": denied_content,
            }

    # 获取真正的 Python 函数
    tool_function = tool_info["function"]

    # 执行工具
    try:
        result = tool_function(**arguments)
        content = serialize_result(result)

    except Exception as error:
        if trace:
            trace.log(
                "tool_failed",
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )

        raise

    # 记录工具成功结果
    if trace:
        trace.log(
            "tool_finished",
            {
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "arguments": arguments,
                "status": "success",
                "result": content,
            },
        )

    return {
        "status": "success",
        "tool_call_id": tool_call.id,
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
        "content": content,
    }