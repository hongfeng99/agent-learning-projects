import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("MODELSCOPE_API_KEY")
base_url = os.getenv("MODELSCOPE_BASE_URL")
model = os.getenv("MODELSCOPE_MODEL")

print("当前 .env 路径：", env_path)
print("是否读取到 MODELSCOPE_API_KEY：", api_key is not None)
print("MODELSCOPE_BASE_URL：", base_url)
print("MODELSCOPE_MODEL：", model)

if not api_key:
    raise RuntimeError("没有读取到 MODELSCOPE_API_KEY，请检查 .env 文件。")

if not base_url:
    raise RuntimeError("没有读取到 MODELSCOPE_BASE_URL，请检查 .env 文件。")

if not model:
    raise RuntimeError("没有读取到 MODELSCOPE_MODEL，请检查 .env 文件。")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "你是一个适合新手学习 Agent 开发的 Python 助教。"
        },
        {
            "role": "user",
            "content": "用一句话解释什么是 Agent。"
        }
    ]
)

print(response.choices[0].message.content)