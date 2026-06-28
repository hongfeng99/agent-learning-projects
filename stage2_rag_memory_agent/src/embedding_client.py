from functools import lru_cache

from sentence_transformers import SentenceTransformer


DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    加载本地 embedding 模型。

    第一次运行会下载模型，之后会使用本地缓存。
    """
    return SentenceTransformer(DEFAULT_EMBEDDING_MODEL)


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """
    将文本列表转换成 embedding 向量。

    这里不再调用远程 API，而是使用本地 sentence-transformers 模型。
    """
    if not texts:
        return []

    embedding_model = get_embedding_model()

    embeddings = embedding_model.encode(
        texts,
        normalize_embeddings=True,
    )

    return embeddings.tolist()