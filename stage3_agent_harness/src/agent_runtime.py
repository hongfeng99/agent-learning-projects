from src.llm_client import call_llm
from src.session_store import SessionStore
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
    session_id: str | None = None,
) -> str:
    """
    运行支持以下能力的 Agent：

    1. 多轮工具调用
    2. 危险工具权限确认
    3. Trace 日志
    4. Session 会话持久化
    """

    trace = TraceLogger()
    session = SessionStore(session_id=session_id)

    print("\nSession ID：")
    print(session.session_id)

    print("\nSession 文件：")
    print(session.path)

    print("\nTrace 文件：")
    print(trace.path)

    # 新会话中还没有消息，
    # 需要先加入 system prompt
    resumed = not session.is_empty

    if session.is_empty:
        session.add_message(
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        )

    # 无论新会话还是旧会话，
    # 都要加入本次用户任务
    session.add_message(
        {
            "role": "user",
            "content": task,
        }
    )

    # messages 指向 SessionStore 中的消息列表
    messages = session.messages

    tools = get_tool_schemas()

    trace.log(
        "run_started",
        {
            "task": task,
            "max_steps": max_steps,
            "tool_count": len(tools),
            "session_id": session.session_id,
            "session_path": str(session.path),
            "resumed": resumed,
            "initial_message_count": len(messages),
        },
    )

    try:
        for step in range(1, max_steps + 1):
            print(f"\n第 {step} 轮")
            print("=" * 50)

            trace.log(
                "model_requested",
                {
                    "agent_step": step,
                    "message_count": len(messages),
                    "session_id": session.session_id,
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

            # 保存模型消息
            session.add_message(assistant_data)

            # 没有工具调用，任务完成
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
                        "session_id": session.session_id,
                        "final_message_count": len(
                            session.messages
                        ),
                    },
                )

                print("\nSession 已保存：")
                print(session.path)

                print("\nTrace 已保存：")
                print(trace.path)

                return final_answer

            # 执行模型申请的工具
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

                # 工具成功、失败或拒绝，
                # 都保存成 tool message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                }

                session.add_message(tool_message)

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
                "session_id": session.session_id,
            },
        )

        print("\nSession 已保存：")
        print(session.path)

        print("\nTrace 已保存：")
        print(trace.path)

        raise