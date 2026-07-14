from pathlib import Path


WORKSPACE = Path("demo_workspace").resolve()


def _safe_path(filename: str) -> Path:
    """
    只允许访问 demo_workspace 目录内的文件，避免 agent 乱读系统文件。
    """
    path = (WORKSPACE / filename).resolve()

    if not str(path).startswith(str(WORKSPACE)):
        raise ValueError("禁止访问 demo_workspace 之外的文件")

    return path


def list_files() -> str:
    """
    列出 demo_workspace 中的文件。
    """
    files = [p.name for p in WORKSPACE.iterdir() if p.is_file()]
    return "\n".join(files) if files else "demo_workspace 为空"


def read_file(filename: str) -> str:
    """
    读取 demo_workspace 中的文件。
    """
    path = _safe_path(filename)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filename}")

    return path.read_text(encoding="utf-8")


def write_file(filename: str, content: str) -> str:
    """
    写入 demo_workspace 中的文件。
    """
    path = _safe_path(filename)
    path.write_text(content, encoding="utf-8")
    return f"已写入文件: {filename}"


def summarize_file(filename: str) -> str:
    """
    一个你自己的工具：读取文件并做一个非常简单的摘要。
    后面可以替换成 LLM 摘要。
    """
    content = read_file(filename)

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    summary = "；".join(lines[:2])

    return f"文件 {filename} 的简要总结：{summary}"