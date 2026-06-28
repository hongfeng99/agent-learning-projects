from pathlib import Path

file_path = Path("data/raw/sample.txt")

text = file_path.read_text(encoding="utf-8")

print("文档路径：", file_path)
print("文档内容：")
print(text)