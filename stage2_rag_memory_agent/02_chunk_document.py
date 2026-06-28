from pathlib import Path


def chunk_text(text: str, chunk_size: int = 120, overlap: int = 30) -> list[str]:
    """
    把长文本切成多个小块。

    chunk_size: 每个 chunk 的最大字符数
    overlap: 相邻 chunk 之间重叠的字符数
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


file_path = Path("data/raw/sample.txt")
text = file_path.read_text(encoding="utf-8")

chunks = chunk_text(text)

print(f"总共切出 {len(chunks)} 个 chunk")

for i, chunk in enumerate(chunks, start=1):
    print(f"\n--- Chunk {i} ---")
    print(chunk)