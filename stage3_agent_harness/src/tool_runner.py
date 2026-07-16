import json
from typing import Any

from src.permission import request_permission
from src.tool_registry import get_tool
from src.trace_logger import TraceLogger


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
        default=str,
    )


def execute_tool_call(
    tool_call,
    trace: TraceLogger | None = None,
) -> dict:
    """
    执行模型产生的一次工具调用。

    流程：
    1. 获取工具名称和原始参数
    2. 解析 JSON 参数
    3. 从注册表查找工具
    4. 检查危险标记
    5. 必要时请求用户授权
    6. 执行 Python 函数
    7. 返回执行结果
    """

    tool_name = tool_call.function.name
    raw_arguments = (
        tool_call.function.arguments or "{}"
    )

    if trace:
        trace.log(
            "tool_requested",
            {
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "raw_arguments": raw_arguments,
            },
        )

    # 将模型返回的 JSON 字符串转换成 Python 字典
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

    # 查找工具注册信息
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

    tool_function = tool_info["function"]

    # 真正执行 Python 工具
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