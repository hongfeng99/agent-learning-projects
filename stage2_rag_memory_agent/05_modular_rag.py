from pathlib import Path

from src.rag_qa import rag_answer


if __name__ == "__main__":
    file_path = Path("data/raw/sample.txt")

    query = input("请输入你的问题：")

    answer = rag_answer(query, file_path)

    print("\n===== RAG 回答 =====")
    print(answer)