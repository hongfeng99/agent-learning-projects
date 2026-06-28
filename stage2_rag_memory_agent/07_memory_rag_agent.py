from pathlib import Path

from src.chunker import chunk_text
from src.document_loader import load_text_file
from src.llm_client import chat
from src.memory_store import format_memories, load_memories, save_memory
from src.rag_qa import build_context
from src.retriever import retrieve


DEFAULT_FILE_PATH = Path("data/raw/sample.txt")


def is_save_memory_command(user_input: str) -> bool:
    """
    判断用户是否想保存一条长期记忆。
    """
    return user_input.startswith("记住：") or user_input.startswith("记住:")


def extract_memory_text(user_input: str) -> str:
    """
    从“记住：xxx”中提取真正要保存的内容。
    """
    if user_input.startswith("记住："):
        return user_input.replace("记住：", "", 1).strip()

    if user_input.startswith("记住:"):
        return user_input.replace("记住:", "", 1).strip()

    return user_input.strip()


def answer_with_memory_and_rag(
    query: str,
    file_path: str | Path = DEFAULT_FILE_PATH,
    top_k: int = 3,
) -> str:
    """
    同时使用长期记忆和 RAG 文档检索来回答问题。
    """
    path = Path(file_path)

    # 1. 读取长期记忆
    memories = load_memories()
    memory_text = format_memories(memories)

    # 2. 读取文档
    text = load_text_file(path)

    # 3. 切分文档
    chunks = chunk_text(text)

    # 4. 检索相关 chunk
    results = retrieve(query, chunks, top_k=top_k)

    # 5. 构建 RAG 上下文
    context = build_context(results, path)

    # 6. 把 memory + context + query 一起发给大模型
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个带长期记忆和 RAG 检索能力的 Agent。"
                "你会收到三部分信息：长期记忆、检索到的资料、用户当前问题。"
                "回答时优先依据检索资料。"
                "长期记忆主要用于理解用户偏好、背景和长期需求。"
                "如果资料中没有答案，就明确说：根据现有资料无法确定。"
                "不要编造资料或记忆中不存在的信息。"
            ),
        },
        {
            "role": "user",
            "content": f"""
下面是用户的长期记忆：

{memory_text}

下面是从文档中检索到的资料：

{context}

用户当前问题：

{query}

请综合长期记忆和检索资料回答用户问题。
""",
        },
    ]

    return chat(messages)


def run_memory_rag_agent() -> None:
    """
    启动一个同时具备 Memory 和 RAG 能力的 Agent。
    """
    print("Memory + RAG Agent 已启动。")
    print("输入示例：记住：我正在学习 Python Agent 开发")
    print("输入示例：什么是 RAG？")
    print("输入 memory 查看当前记忆。")
    print("输入 exit 退出。")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Agent：再见。")
            break

        if not user_input:
            continue

        if user_input.lower() in ["memory", "memories", "查看记忆"]:
            memories = load_memories()
            print("\n===== 当前长期记忆 =====")
            print(format_memories(memories))
            continue

        if is_save_memory_command(user_input):
            memory_text = extract_memory_text(user_input)

            if not memory_text:
                print("Agent：你想让我记住什么？")
                continue

            memory = save_memory(memory_text)
            print(f"Agent：已记住：{memory['text']}")
            continue

        answer = answer_with_memory_and_rag(user_input)

        print("\nAgent：")
        print(answer)


if __name__ == "__main__":
    run_memory_rag_agent()