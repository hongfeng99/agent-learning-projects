from pathlib import Path

from src.chunker import chunk_text
from src.document_loader import load_text_file
from src.embedding_retriever import (
    build_embedding_index,
    load_embedding_index,
    retrieve_by_embedding,
)
from src.llm_client import chat


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

    例如：
    [1] 来源: data/raw/sample.txt, Chunk ID: 3, Score: 0.8123
    文本内容...
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


def rag_answer_with_citations(
    query: str,
    top_k: int = 3,
    min_score: float = 0.25,
) -> str:
    """
    使用 embedding 检索 + 引用来源的 RAG 问答。
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


def main() -> None:
    print("RAG with Citations 已启动。")
    print("输入问题后，会基于 embedding 检索结果回答，并输出引用来源。")
    print("输入 exit 退出。")

    while True:
        query = input("\n请输入问题：").strip()

        if query.lower() in ["exit", "quit", "q"]:
            print("退出。")
            break

        if not query:
            continue

        answer = rag_answer_with_citations(query)

        print("\n===== 回答 =====")
        print(answer)


if __name__ == "__main__":
    main()