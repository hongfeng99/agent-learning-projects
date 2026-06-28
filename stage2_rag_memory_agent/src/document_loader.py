from pathlib import Path


def load_text_file(file_path: str | Path) -> str:
    """
    读取 txt 文档内容。
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    return path.read_text(encoding="utf-8")