import json
import math
from pathlib import Path

from src.embedding_client import embed_texts


DEFAULT_INDEX_PATH = Path("data/index/embeddings.json")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    计算两个向量的余弦相似度。
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def build_embedding_index(
    chunks: list[str],
    index_path: str | Path = DEFAULT_INDEX_PATH,
) -> list[dict]:
    """
    给 chunks 生成 embedding，并保存到本地 JSON 文件。
    """
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    embeddings = embed_texts(chunks)

    index = []

    for i, chunk in enumerate(chunks):
        index.append(
            {
                "chunk_id": i + 1,
                "text": chunk,
                "embedding": embeddings[i],
            }
        )

    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return index


def load_embedding_index(
    index_path: str | Path = DEFAULT_INDEX_PATH,
) -> list[dict]:
    """
    读取本地 embedding index。
    """
    index_path = Path(index_path)

    if not index_path.exists():
        raise FileNotFoundError(f"找不到索引文件：{index_path}")

    return json.loads(index_path.read_text(encoding="utf-8"))


def retrieve_by_embedding(
    query: str,
    index: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    用 embedding 相似度检索最相关的 chunks。
    """
    query_embedding = embed_texts([query])[0]

    results = []

    for item in index:
        score = cosine_similarity(query_embedding, item["embedding"])

        results.append(
            {
                "chunk_id": item["chunk_id"],
                "score": score,
                "text": item["text"],
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]