from pathlib import Path

from src.llm_client import chat


def chunk_text(text: str, chunk_size: int = 120, overlap: int = 30) -> list[str]:
    """
    把长文本切成多个小块。
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

    return chunks


def simple_score(query: str, chunk: str) -> int:
    """
    最简单的关键词检索打分。
    用户问题中的字符在 chunk 里出现得越多，分数越高。
    """
    score = 0

    for char in query:
        if char.strip() and char in chunk:
            score += 1

    return score


def retrieve(query: str, chunks: list[str], top_k: int = 3) -> list[dict]:
    """
    从 chunks 中检索最相关的 top_k 个片段。
    """
    scored_chunks = []

    for i, chunk in enumerate(chunks):
        score = simple_score(query, chunk)

        scored_chunks.append(
            {
                "chunk_id": i + 1,
                "score": score,
                "text": chunk,
            }
        )

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    return scored_chunks[:top_k]


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


def rag_answer(query: str, file_path: Path) -> str:
    """
    RAG 主流程：
    1. 读取文档
    2. 切分文档
    3. 检索相关片段
    4. 把片段交给大模型回答
    """
    text = file_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)

    results = retrieve(query, chunks, top_k=3)
    context = build_context(results, file_path)

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

    answer = chat(messages)

    return answer


if __name__ == "__main__":
    file_path = Path("data/raw/sample.txt")

    query = input("请输入你的问题：")

    answer = rag_answer(query, file_path)

    print("\n===== RAG 回答 =====")
    print(answer)