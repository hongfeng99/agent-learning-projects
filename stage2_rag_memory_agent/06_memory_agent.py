from src.llm_client import chat
from src.memory_store import format_memories, load_memories, save_memory


def is_save_memory_command(user_input: str) -> bool:
    """
    判断用户是否在要求保存记忆。
    """
    return user_input.startswith("记住：") or user_input.startswith("记住:")


def extract_memory_text(user_input: str) -> str:
    """
    从“记住：xxx”中提取 xxx。
    """
    if user_input.startswith("记住："):
        return user_input.replace("记住：", "", 1).strip()

    if user_input.startswith("记住:"):
        return user_input.replace("记住:", "", 1).strip()

    return user_input.strip()


def answer_with_memory(user_input: str) -> str:
    """
    读取长期记忆，并让大模型基于记忆回答用户问题。
    """
    memories = load_memories()
    memory_text = format_memories(memories)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个带长期记忆的 Agent。"
                "你会收到用户的长期记忆和用户当前问题。"
                "如果问题可以根据记忆回答，就根据记忆回答。"
                "如果记忆里没有相关信息，就说明记忆中没有相关内容。"
                "不要编造记忆中不存在的信息。"
            ),
        },
        {
            "role": "user",
            "content": f"""
下面是当前保存的长期记忆：

{memory_text}

用户当前问题：
{user_input}

请根据长期记忆回答用户问题。
""",
        },
    ]

    return chat(messages)


def run_memory_agent() -> None:
    """
    启动一个简单的记忆 Agent。
    """
    print("Memory Agent 已启动。")
    print("输入示例：记住：我正在学习 Python Agent 开发")
    print("输入 exit 退出。")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Agent：再见。")
            break

        if not user_input:
            continue

        if is_save_memory_command(user_input):
            memory_text = extract_memory_text(user_input)

            if not memory_text:
                print("Agent：你想让我记住什么？")
                continue

            memory = save_memory(memory_text)

            print(f"Agent：已记住：{memory['text']}")
            continue

        answer = answer_with_memory(user_input)

        print("\nAgent：")
        print(answer)


if __name__ == "__main__":
    run_memory_agent()