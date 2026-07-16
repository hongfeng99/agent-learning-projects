from src.llm_client import call_llm
from src.tool_registry import get_tool_schemas
from src.tool_runner import execute_tool_call
from src.trace_logger import TraceLogger


DEFAULT_MAX_STEPS = 8


SYSTEM_PROMPT = """
你是一个文件管理 Agent。

你可以使用提供的工具完成用户任务。

工作规则：
1. 涉及工作区真实文件时，必须调用工具，不要猜测。
2. 根据前一步工具结果决定下一步操作。
3. 工具失败时，阅读错误信息并决定如何处理。
4. 如果工具结果表明用户拒绝授权，不要重复申请同一个操作。
5. 任务完成后，用中文给出简洁、明确的最终回答。
6. 除非用户明确要求，否则不要写入或修改文件。
""".strip()


def run_agent(
    task: str,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> str:
    """
    运行支持多轮工具调用的 Agent。
    """

    # 每次运行创建一个新的 Trace 文件
    trace = TraceLogger()

    print("\nTrace 文件：")
    print(trace.path)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": task,
        },
    ]

    tools = get_tool_schemas()

    # 记录整个 Agent 开始运行
    trace.log(
        "run_started",
        {
            "task": task,
            "max_steps": max_steps,
            "tool_count": len(tools),
        },
    )

    try:
        for step in range(1, max_steps + 1):
            print(f"\n第 {step} 轮")
            print("=" * 50)

            # 记录即将请求模型
            trace.log(
                "model_requested",
                {
                    "agent_step": step,
                    "message_count": len(messages),
                },
            )

            assistant_message = call_llm(
                messages=messages,
                tools=tools,
            )

            assistant_data = (
                assistant_message.model_dump(
                    exclude_none=True
                )
            )

            # 记录模型返回内容
            trace.log(
                "model_responded",
                {
                    "agent_step": step,
                    "message": assistant_data,
                },
            )

            print(
                "模型文本：",
                assistant_message.content,
            )
            print(
                "工具调用：",
                assistant_message.tool_calls,
            )

            # 将模型消息加入上下文
            messages.append(assistant_data)

            # 没有工具调用，说明模型给出了最终回答
            if not assistant_message.tool_calls:
                final_answer = (
                    assistant_message.content
                    or "模型没有返回最终内容。"
                )

                trace.log(
                    "final_answer",
                    {
                        "agent_step": step,
                        "content": final_answer,
                    },
                )

                trace.log(
                    "run_finished",
                    {
                        "status": "success",
                        "agent_steps": step,
                    },
                )

                print("\nTrace 已保存：")
                print(trace.path)

                return final_answer

            # 执行本轮所有工具调用
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name

                print(
                    f"\n准备执行工具：{tool_name}"
                )

                try:
                    execution = execute_tool_call(
                        tool_call,
                        trace=trace,
                    )

                    tool_content = execution["content"]

                    print(
                        "执行状态：",
                        execution["status"],
                    )
                    print(
                        "工具参数：",
                        execution["arguments"],
                    )
                    print("工具结果：")
                    print(tool_content)

                except Exception as error:
                    # 工具失败后不立即终止 Agent，
                    # 而是把错误交给模型
                    tool_content = (
                        f"工具 {tool_name} 执行失败："
                        f"{type(error).__name__}: {error}"
                    )

                    print(tool_content)

                    trace.log(
                        "tool_error_returned_to_model",
                        {
                            "tool_call_id": tool_call.id,
                            "tool_name": tool_name,
                            "content": tool_content,
                        },
                    )

                # 把工具结果加入 messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_content,
                    }
                )

        # 超过最大轮数仍未完成
        raise RuntimeError(
            f"Agent 已达到最大步数 {max_steps}，"
            "但任务仍未完成。"
        )

    except Exception as error:
        trace.log(
            "run_failed",
            {
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )

        print("\nTrace 已保存：")
        print(trace.path)

        raise