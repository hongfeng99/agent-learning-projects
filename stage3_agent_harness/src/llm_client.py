import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 当前文件位于：
# stage3_agent_harness/src/llm_client.py
#
# parent       -> src
# parent.parent -> stage3_agent_harness
PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_DIR / ".env"

# 读取 stage3_agent_harness/.env
load_dotenv(ENV_PATH)


API_KEY = os.getenv("MODELSCOPE_API_KEY")
BASE_URL = os.getenv("MODELSCOPE_BASE_URL")
MODEL = os.getenv("MODELSCOPE_MODEL")


if not API_KEY:
    raise RuntimeError(
        "没有读取到 MODELSCOPE_API_KEY，"
        "请检查 stage3_agent_harness/.env"
    )

if not BASE_URL:
    raise RuntimeError(
        "没有读取到 MODELSCOPE_BASE_URL，"
        "请检查 stage3_agent_harness/.env"
    )

if not MODEL:
    raise RuntimeError(
        "没有读取到 MODELSCOPE_MODEL，"
        "请检查 stage3_agent_harness/.env"
    )


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


def call_llm(messages: list[dict], tools: list[dict] | None = None):
    """
    调用大模型。

    当前第一步只传 messages，完成普通对话测试。

    后续接入 Agent Loop 时，还可以传入 tools，
    让模型自主选择工具。
    """

    request_args = {
        "model": MODEL,
        "messages": messages,
    }

    # 只有真正传入工具时，才向模型请求中添加 tools
    if tools:
        request_args["tools"] = tools
        request_args["tool_choice"] = "auto"

    response = client.chat.completions.create(**request_args)

    return response.choices[0].message