import json
from pydantic import BaseModel
from llm_client import client, model


class TaskJudge(BaseModel):
    task_type: str
    need_tool: bool
    reason: str


messages = [
    {
        "role": "system",
        "content": """
你是一个任务分类器。
你必须只输出 JSON，不要输出 Markdown，不要输出解释文字。

JSON 格式如下：
{
  "task_type": "chat | calculate | search | read_file | other",
  "need_tool": true,
  "reason": "判断理由"
}
"""
    },
    {
        "role": "user",
        "content": "帮我计算 23 * 17。"
    }
]


response = client.chat.completions.create(
    model=model,
    messages=messages,
)

content = response.choices[0].message.content

print("模型原始输出：")
print(content)

data = json.loads(content)
result = TaskJudge(**data)

print("\n解析后的结构化对象：")
print(result)

print("\n字段读取：")
print("任务类型：", result.task_type)
print("是否需要工具：", result.need_tool)
print("原因：", result.reason)