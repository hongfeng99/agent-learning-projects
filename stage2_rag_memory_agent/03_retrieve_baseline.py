from pathlib import Path


def chunk_text(text: str, chunk_size: int = 120, overlap: int = 30) -> list[str]:
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
    最简单的关键词匹配打分：
    用户问题里的字符，在 chunk 中出现得越多，分数越高。
    """
    score = 0

    for char in query:
        if char.strip() and char in chunk:
            score += 1

    return score


def retrieve(query: str, chunks: list[str], top_k: int = 3) -> list[tuple[int, int, str]]:
    scored_chunks = []

    for i, chunk in enumerate(chunks):
        score = simple_score(query, chunk)
        scored_chunks.append((i, score, chunk))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return scored_chunks[:top_k]


file_path = Path("data/raw/sample.txt")
text = file_path.read_text(encoding="utf-8")

chunks = chunk_text(text)

query = input("请输入你的问题：")

results = retrieve(query, chunks)

print("\n检索结果：")

for rank, result in enumerate(results, start=1):
    chunk_id, score, chunk = result

    print(f"\n--- Top {rank} | Chunk {chunk_id + 1} | Score: {score} ---")
    print(chunk)