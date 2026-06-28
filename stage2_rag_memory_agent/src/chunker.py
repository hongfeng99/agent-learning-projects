def chunk_text(text: str, chunk_size: int = 120, overlap: int = 30) -> list[str]:
    """
    把长文本切成多个 chunk。

    text: 原始长文本
    chunk_size: 每个 chunk 的最大字符数
    overlap: 相邻 chunk 的重叠字符数
    """
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

    return chunks