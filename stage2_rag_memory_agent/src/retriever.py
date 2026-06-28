def simple_score(query: str, chunk: str) -> int:
    """
    最简单的字符匹配检索分数。
    用户问题中的字符出现在 chunk 中越多，分数越高。
    """
    stop_chars = set("的是什么？?，,。.!！ ")

    score = 0

    for char in query:
        if char in stop_chars:
            continue

        if char in chunk:
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