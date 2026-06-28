from pathlib import Path

from src.chunker import chunk_text
from src.document_loader import load_text_file
from src.llm_client import chat
from src.retriever import retrieve


def build_context(results: list[dict], file_path: Path) -> str:
    """
    把检索结果整理成给大模型看的上下文。
    """
    context_parts = []

    for result in results:
        chunk_id = result["chunk_id"]
        text = result["text"]

        context_parts.append(
            f"[来源: {file_path}, Chunk {chunk_id}]\n{text}"
        )

    return "\n\n".join(context_parts)


def rag_answer(query: str, file_path: str | Path, top_k: int = 3) -> str:
    """
    RAG 问答主流程：
    1. 读取文档
    2. 切分 chunks
    3. 检索相关 chunks
    4. 构建 context
    5. 调用大模型回答
    """
    path = Path(file_path)

    text = load_text_file(path)
    chunks = chunk_text(text)

    results = retrieve(query, chunks, top_k=top_k)
    context = build_context(results, path)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个严谨的 RAG 问答助手。"
                "你只能根据用户提供的资料回答问题。"
                "如果资料中没有答案，就回答：根据现有资料无法确定。"
                "回答时要尽量简洁，并在最后列出引用来源。"
            ),
        },
        {
            "role": "user",
            "content": f"""
下面是检索到的资料：

{context}

用户问题：
{query}

请根据上面的资料回答问题。
""",
        },
    ]

    return chat(messages)