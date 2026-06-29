from src.llm_client import chat
from src.memory_store import format_memories, load_memories, save_memory


MAX_SHORT_TERM_MESSAGES = 6


def save_long_term_memory(user_input: str) -> str:
    """
    保存长期记忆。

    用户输入：
        记住：我正在学习 Python Agent 开发

    保存内容：
        我正在学习 Python Agent 开发
    """
    if user_input.startswith("记住："):
        memory_text = user_input.replace("记住：", "", 1).strip()
    elif user_input.startswith("记住:"):
        memory_text = user_input.replace("记住:", "", 1).strip()
    else:
        memory_text = user_input.strip()

    if not memory_text:
        return "你想让我记住什么？"

    memory = save_memory(memory_text)

    return f"已保存长期记忆：{memory['text']}"


def get_short_term_context(conversation_history: list[dict]) -> str:
    """
    获取短期上下文。

    短期上下文就是当前程序运行期间最近几轮对话。
    它不会永久保存，程序关闭后就消失。
    """
    if not conversation_history:
        return "暂无短期上下文。"

    recent_messages = conversation_history[-MAX_SHORT_TERM_MESSAGES:]

    lines = []

    for message in recent_messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            lines.append(f"用户：{content}")
        elif role == "assistant":
            lines.append(f"Agent：{content}")

    return "\n".join(lines)


def update_session_summary(
    old_summary: str,
    conversation_history: list[dict],
) -> str:
    """
    更新会话记忆。

    会话记忆不是完整聊天记录，而是当前会话的摘要。
    它比短期上下文更压缩，但比长期记忆更临时。
    """
    if not conversation_history:
        return old_summary or "当前会话还没有可总结内容。"

    recent_context = get_short_term_context(conversation_history)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个会话摘要助手。"
                "你的任务是把当前对话压缩成简洁的会话记忆。"
                "保留用户当前目标、已经完成的步骤、遇到的问题、下一步计划。"
                "不要编造对话中没有出现的信息。"
            ),
        },
        {
            "role": "user",
            "content": f"""
旧的会话摘要：

{old_summary or "暂无"}

最近对话：

{recent_context}

请生成更新后的会话摘要。
要求：
1. 用中文。
2. 控制在 5 条以内。
3. 保留对后续继续任务有帮助的信息。
""",
        },
    ]

    return chat(messages)


def build_memory_prompt(
    user_input: str,
    short_term_context: str,
    session_summary: str,
    long_term_memory: str,
) -> list[dict]:
    """
    构建包含三种记忆的 prompt。
    """
    return [
        {
            "role": "system",
            "content": (
                "你是一个用于演示 Agent Memory 的助手。"
                "你会同时收到三类记忆：短期上下文、会话记忆、长期记忆。"
                "短期上下文用于理解当前几轮对话。"
                "会话记忆用于理解本次会话的阶段性摘要。"
                "长期记忆用于理解用户长期偏好和长期背景。"
                "回答时要综合三类记忆，但不要编造记忆中不存在的信息。"
            ),
        },
        {
            "role": "user",
            "content": f"""
【短期上下文】
{short_term_context}

【会话记忆】
{session_summary or "暂无会话记忆。"}

【长期记忆】
{long_term_memory}

【用户当前输入】
{user_input}

请基于以上信息回答用户。
""",
        },
    ]


def run_memory_types_agent() -> None:
    """
    演示三种 memory：
    1. 短期上下文：conversation_history
    2. 会话记忆：session_summary
    3. 长期记忆：memory/memory.json
    """
    conversation_history = []
    session_summary = ""

    print("Memory Types Agent 已启动。")
    print("这个文件用于演示三种记忆：短期上下文、会话记忆、长期记忆。")
    print("命令：")
    print("1. 记住：xxx      保存长期记忆")
    print("2. 查看短期上下文")
    print("3. 查看会话记忆")
    print("4. 更新会话记忆")
    print("5. 查看长期记忆")
    print("6. exit          退出")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Agent：再见。")
            break

        if not user_input:
            continue

        if user_input.startswith("记住：") or user_input.startswith("记住:"):
            result = save_long_term_memory(user_input)
            print(f"Agent：{result}")

            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": result})
            continue

        if user_input == "查看短期上下文":
            short_term_context = get_short_term_context(conversation_history)
            print("\n===== 短期上下文 =====")
            print(short_term_context)
            continue

        if user_input == "查看会话记忆":
            print("\n===== 会话记忆 =====")
            print(session_summary or "暂无会话记忆。")
            continue

        if user_input == "更新会话记忆":
            session_summary = update_session_summary(
                session_summary,
                conversation_history,
            )
            print("\n===== 已更新会话记忆 =====")
            print(session_summary)
            continue

        if user_input == "查看长期记忆":
            memories = load_memories()
            print("\n===== 长期记忆 =====")
            print(format_memories(memories))
            continue

        short_term_context = get_short_term_context(conversation_history)
        long_term_memory = format_memories(load_memories())

        messages = build_memory_prompt(
            user_input=user_input,
            short_term_context=short_term_context,
            session_summary=session_summary,
            long_term_memory=long_term_memory,
        )

        answer = chat(messages)

        print("\nAgent：")
        print(answer)

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    run_memory_types_agent()