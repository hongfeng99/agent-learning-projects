import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 当前文件路径：
# D:\agent-learning-projects\stage2_rag_memory_agent\src\llm_client.py
CURRENT_FILE = Path(__file__).resolve()

# Stage2 目录：
# D:\agent-learning-projects\stage2_rag_memory_agent
STAGE2_DIR = CURRENT_FILE.parents[1]

# 项目根目录：
# D:\agent-learning-projects
PROJECT_ROOT = CURRENT_FILE.parents[2]


# 优先读取项目根目录的 .env
load_dotenv(PROJECT_ROOT / ".env")

# 如果 stage2 目录下也有 .env，也可以读取；后读取的不会强制覆盖已有变量
load_dotenv(STAGE2_DIR / ".env")


def get_client() -> OpenAI:
    api_key = (
        os.getenv("MODELSCOPE_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("QWEN_API_KEY")
    )

    base_url = (
        os.getenv("MODELSCOPE_BASE_URL")
        or os.getenv("QWEN_BASE_URL")
        or "https://api-inference.modelscope.cn/v1"
    )

    if not api_key:
        raise RuntimeError(
            "没有找到 API Key。请检查根目录 .env 中是否设置了 MODELSCOPE_API_KEY=你的key"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    return client


def chat(messages: list[dict], model: str | None = None) -> str:
    client = get_client()

    model_name = (
        model
        or os.getenv("MODELSCOPE_MODEL")
        or os.getenv("QWEN_MODEL")
        or "Qwen/Qwen3.5-35B-A3B"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
    )

    return response.choices[0].message.content