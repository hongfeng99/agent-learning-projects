from pathlib import Path

from src.chunker import chunk_text
from src.document_loader import load_text_file
from src.embedding_retriever import (
    build_embedding_index,
    load_embedding_index,
    retrieve_by_embedding,
)
from src.llm_client import chat
from src.memory_store import format_memories, load_memories, save_memory


DOC_PATH = Path("data/raw/sample.txt")
INDEX_PATH = Path("data/index/embeddings.json")


def prepare_index() -> list[dict]:
    """
    如果已有 embedding index，就读取；
    如果没有，就读取文档、切分文档、构建 embedding index。
    """
    if INDEX_PATH.exists():
        return load_embedding_index(INDEX_PATH)

    text = load_text_file(DOC_PATH)
    chunks = chunk_text(text)

    return build_embedding_index(chunks, INDEX_PATH)


def build_cited_context(results: list[dict], source_path: Path) -> str:
    """
    把检索结果转换成带编号引用的上下文。
    """
    context_parts = []

    for i, item in enumerate(results, start=1):
        chunk_id = item["chunk_id"]
        score = item["score"]
        text = item["text"]

        context_parts.append(
            f"[{i}] 来源: {source_path}, Chunk ID: {chunk_id}, Score: {score:.4f}\n"
            f"{text}"
        )

    return "\n\n".join(context_parts)


def build_sources(results: list[dict], source_path: Path) -> str:
    """
    构建最终展示用的引用来源列表。
    """
    source_lines = []

    for i, item in enumerate(results, start=1):
        source_lines.append(
            f"[{i}] {source_path} - Chunk ID: {item['chunk_id']} - Score: {item['score']:.4f}"
        )

    return "\n".join(source_lines)


def rag_tool(query: str, top_k: int = 3, min_score: float = 0.25) -> str:
    """
    工具 1：RAG 问答工具。
    输入用户问题，输出带引用来源的答案。
    """
    index = prepare_index()

    results = retrieve_by_embedding(query, index, top_k=top_k)

    if not results:
        return "根据现有资料无法确定，因为没有检索到相关内容。"

    best_score = results[0]["score"]

    if best_score < min_score:
        return (
            "根据现有资料无法确定。\n\n"
            f"原因：最高相似度分数只有 {best_score:.4f}，低于阈值 {min_score}。"
        )

    context = build_cited_context(results, DOC_PATH)
    sources = build_sources(results, DOC_PATH)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个严谨的 RAG 问答助手。"
                "你只能根据用户提供的检索资料回答问题。"
                "如果资料中没有答案，就说“根据现有资料无法确定”。"
                "回答关键结论时必须使用 [1]、[2] 这样的引用编号。"
                "不要编造没有出现在资料中的信息。"
            ),
        },
        {
            "role": "user",
            "content": f"""
下面是检索到的资料：

{context}

用户问题：

{query}

请基于资料回答问题。
要求：
1. 回答必须带引用编号，例如：[1]。
2. 不要使用资料以外的信息。
3. 如果资料不足，就明确说根据现有资料无法确定。
""",
        },
    ]

    answer = chat(messages)

    return f"{answer}\n\n引用来源：\n{sources}"


def save_memory_tool(text: str) -> str:
    """
    工具 2：保存长期记忆。
    """
    memory = save_memory(text)
    return f"已保存长期记忆：{memory['text']}"


def read_memory_tool() -> str:
    """
    工具 3：读取长期记忆。
    """
    memories = load_memories()
    return format_memories(memories)


def choose_tool(user_input: str) -> str:
    """
    一个非常简单的工具选择器。

    这里先不用 function calling，
    先用规则判断用户想调用哪个工具。
    """
    text = user_input.strip()

    if text.startswith("记住：") or text.startswith("记住:"):
        return "save_memory"

    if text in ["memory", "memories", "查看记忆", "读取记忆"]:
        return "read_memory"

    return "rag"


def extract_memory_text(user_input: str) -> str:
    """
    从 “记住：xxx” 中提取要保存的记忆内容。
    """
    if user_input.startswith("记住："):
        return user_input.replace("记住：", "", 1).strip()

    if user_input.startswith("记住:"):
        return user_input.replace("记住:", "", 1).strip()

    return user_input.strip()


def run_toolified_agent() -> None:
    """
    启动工具化 RAG + Memory Agent。
    """
    print("Toolified RAG Agent 已启动。")
    print("可用工具：")
    print("1. save_memory_tool：保存长期记忆")
    print("2. read_memory_tool：读取长期记忆")
    print("3. rag_tool：基于资料进行 RAG 问答")
    print("输入 exit 退出。")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Agent：再见。")
            break

        if not user_input:
            continue

        tool_name = choose_tool(user_input)

        print(f"\n[Agent 选择工具] {tool_name}")

        if tool_name == "save_memory":
            memory_text = extract_memory_text(user_input)

            if not memory_text:
                print("Agent：你想让我记住什么？")
                continue

            result = save_memory_tool(memory_text)
            print(f"Agent：{result}")
            continue

        if tool_name == "read_memory":
            result = read_memory_tool()
            print("\nAgent：当前长期记忆如下：")
            print(result)
            continue

        if tool_name == "rag":
            result = rag_tool(user_input)
            print("\nAgent：")
            print(result)
            continue


if __name__ == "__main__":
    run_toolified_agent()