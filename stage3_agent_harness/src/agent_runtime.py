from src.llm_client import call_llm
from src.tool_registry import get_tool_schemas
from src.tool_runner import execute_tool_call


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
    运行一个支持多轮工具调用的 Agent。

    每一轮流程：

    1. 调用模型
    2. 判断模型是否请求工具
    3. 如果没有工具调用，返回最终答案
    4. 如果有工具调用，执行工具
    5. 把工具结果加入 messages
    6. 进入下一轮
    """

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

    for step in range(1, max_steps + 1):
        print(f"\n第 {step} 轮")
        print("=" * 50)

        # 模型根据当前消息和工具结果，
        # 决定是继续调用工具，还是直接回答
        assistant_message = call_llm(
            messages=messages,
            tools=tools,
        )

        print("模型文本：", assistant_message.content)
        print("工具调用：", assistant_message.tool_calls)

        # 保存模型本轮消息
        messages.append(
            assistant_message.model_dump(
                exclude_none=True
            )
        )

        # 没有工具调用，说明模型认为任务已经完成
        if not assistant_message.tool_calls:
            return assistant_message.content or "模型没有返回最终内容。"

        # 模型一次可能请求多个工具，所以需要遍历
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name

            print(f"\n准备执行工具：{tool_name}")

            try:
                execution = execute_tool_call(tool_call)

                tool_content = execution["content"]

                print("执行状态：", execution["status"])
                print("工具参数：", execution["arguments"])
                print("工具结果：")
                print(tool_content)

            except Exception as error:
                # 暂时不让整个 Agent 直接退出，
                # 而是把错误信息交给模型判断下一步
                tool_content = (
                    f"工具 {tool_name} 执行失败："
                    f"{type(error).__name__}: {error}"
                )

                print(tool_content)

            # 工具成功或失败，都作为 tool message
            # 返回给模型
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                }
            )

    raise RuntimeError(
        f"Agent 已达到最大步数 {max_steps}，"
        "但任务仍未完成。"
    )