from pathlib import Path

from src.chunker import chunk_text
from src.document_loader import load_text_file
from src.embedding_retriever import (
    build_embedding_index,
    load_embedding_index,
    retrieve_by_embedding,
)


DOC_PATH = Path("data/raw/sample.txt")
INDEX_PATH = Path("data/index/embeddings.json")


def prepare_index() -> list[dict]:
    """
    如果已有 embedding index，就直接读取；
    如果没有，就读取文档、切分、生成 embedding index。
    """
    if INDEX_PATH.exists():
        print(f"发现已有索引文件：{INDEX_PATH}")
        return load_embedding_index(INDEX_PATH)

    print("未发现索引文件，开始构建 embedding index...")

    text = load_text_file(DOC_PATH)
    chunks = chunk_text(text)

    index = build_embedding_index(chunks, INDEX_PATH)

    print(f"索引构建完成，共 {len(index)} 个 chunks。")
    return index


def main() -> None:
    index = prepare_index()

    print("\nEmbedding Retriever 已启动。")
    print("输入问题后，会返回最相关的 chunks。")
    print("输入 exit 退出。")

    while True:
        query = input("\n请输入问题：").strip()

        if query.lower() in ["exit", "quit", "q"]:
            print("退出。")
            break

        if not query:
            continue

        results = retrieve_by_embedding(query, index, top_k=3)

        print("\n===== 检索结果 =====")

        for result in results:
            print(f"\nChunk ID: {result['chunk_id']}")
            print(f"Score: {result['score']:.4f}")
            print(result["text"])


if __name__ == "__main__":
    main()