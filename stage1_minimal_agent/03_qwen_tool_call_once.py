import json
from llm_client import client, model


def calculator(a: float, b: float, operator: str) -> float:
    """
    一个简单计算器工具。
    支持加、减、乘、除。
    """
    if operator == "add":
        return a + b

    if operator == "sub":
        return a - b

    if operator == "mul":
        return a * b

    if operator == "div":
        return a / b

    raise ValueError(f"不支持的运算符：{operator}")


def call_function(name: str, args: dict):
    """
    工具路由函数。
    模型告诉我们要调用哪个工具，Python 在这里真正执行。
    """
    if name == "calculator":
        return calculator(**args)

    raise ValueError(f"未知工具：{name}")


tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算两个数字的加减乘除。",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "第一个数字"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个数字"
                    },
                    "operator": {
                        "type": "string",
                        "enum": ["add", "sub", "mul", "div"],
                        "description": "运算类型：add 加法，sub 减法，mul 乘法，div 除法"
                    }
                },
                "required": ["a", "b", "operator"]
            }
        }
    }
]


messages = [
    {
        "role": "system",
        "content": "你是一个会使用工具的助手。遇到数学计算时，优先调用 calculator 工具。"
    },
    {
        "role": "user",
        "content": "请使用工具计算 23 * 17。"
    }
]


# 第一次请求模型：让模型判断是否需要调用工具
response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)

assistant_message = response.choices[0].message

print("模型第一次返回：")
print(assistant_message)

# 把模型的 assistant 消息加入上下文
messages.append(assistant_message.model_dump(exclude_none=True))


# 取出模型请求调用的工具
tool_calls = assistant_message.tool_calls

if not tool_calls:
    print("模型没有调用工具，直接回答：")
    print(assistant_message.content)
else:
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        print("\n模型请求调用工具：")
        print("工具名：", tool_name)
        print("参数：", tool_args)

        # Python 真正执行工具
        result = call_function(tool_name, tool_args)

        print("Python 工具执行结果：", result)

        # 把工具结果加入 messages，发回给模型
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
        )

    # 第二次请求模型：让模型根据工具结果生成最终回答
    final_response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
    )

    final_answer = final_response.choices[0].message.content

    print("\n模型最终回答：")
    print(final_answer)