from src.llm_client import MODEL, call_llm
from src.tool_registry import get_tool_schemas
from src.tool_runner import execute_tool_call


def main():
    print("Stage3 Tool Calling 闭环测试")
    print("=" * 50)
    print(f"当前模型：{MODEL}")

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个文件管理 Agent。"
                "你可以根据用户要求选择合适的工具。"
                "当任务需要查看工作区文件时，应调用工具，"
                "不要猜测文件内容。"
                "拿到工具结果后，请用中文回答用户。"
            ),
        },
        {
            "role": "user",
            "content": "请查看当前工作区中有哪些文件。",
        },
    ]

    tools = get_tool_schemas()

    try:
        # --------------------------------
        # 第一次调用模型：决定是否使用工具
        # --------------------------------
        assistant_message = call_llm(
            messages=messages,
            tools=tools,
        )

        print("\n第一次模型返回：")
        print("普通文本：", assistant_message.content)
        print("工具调用：", assistant_message.tool_calls)

        # 如果模型没有调用工具，直接输出模型回答
        if not assistant_message.tool_calls:
            print("\n最终回答：")
            print(assistant_message.content)
            return

        # --------------------------------
        # 保存 assistant 的工具调用消息
        # --------------------------------
        messages.append(
            assistant_message.model_dump(
                exclude_none=True
            )
        )

        # --------------------------------
        # Python 执行模型选择的工具
        # --------------------------------
        for tool_call in assistant_message.tool_calls:
            execution = execute_tool_call(tool_call)

            print("\n执行工具：")
            print(f"工具名称：{execution['tool_name']}")
            print(f"工具参数：{execution['arguments']}")
            print("工具结果：")
            print(execution["content"])

            # 将工具执行结果加入 messages
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": execution["tool_call_id"],
                    "content": execution["content"],
                }
            )

        # --------------------------------
        # 第二次调用模型：根据工具结果回答
        # --------------------------------
        final_message = call_llm(
            messages=messages,
            tools=tools,
        )

        print("\n最终回答：")
        print(final_message.content)

    except Exception as error:
        print("\n运行失败：")
        print(f"{type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    main()