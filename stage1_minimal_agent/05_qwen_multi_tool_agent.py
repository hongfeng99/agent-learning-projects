import json
import time
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
        if b == 0:
            raise ValueError("除数不能为 0")
        return a / b

    raise ValueError(f"不支持的运算符：{operator}")

def fake_search(query: str) -> str:
    """
    模拟搜索工具。
    注意：这不是真正联网搜索，只是为了练习多工具调用。
    """
    fake_database = {
        "Agent": "Agent 是一种能够根据目标，自主调用工具、处理信息并完成任务的程序。",
        "Agent Loop": "Agent Loop 通常指：模型思考、决定行动、调用工具、观察结果、继续推理，直到完成任务。",
        "tool calling": "Tool calling 是指模型根据任务需要，生成工具调用请求，由程序执行真实工具后再把结果返回给模型。",
        "RAG": "RAG 是 Retrieval-Augmented Generation，意思是检索增强生成，常用于让模型基于外部知识回答问题。"
    }

    for keyword, answer in fake_database.items():
        if keyword.lower() in query.lower():
            return answer

    return f"没有找到和「{query}」完全匹配的资料。这是模拟搜索结果。"

def call_function(name: str, args: dict):
    """
    工具路由函数。
    模型告诉我们工具名和参数，Python 在这里真正执行对应工具。
    """
    if name == "calculator":
        return calculator(**args)

    if name == "fake_search":
        return fake_search(**args)

    raise ValueError(f"未知工具：{name}")

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算两个数字的加减乘除。遇到明确数学计算时使用。",
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
    },
    {
        "type": "function",
        "function": {
            "name": "fake_search",
            "description": "模拟搜索资料。遇到用户要求搜索、查询、了解概念、查资料时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户想查询的关键词或问题"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def run_agent(user_input: str, max_steps: int = 5, timeout_seconds: int = 30):
    """
    最小 Agent Loop：
    1. 用户输入
    2. 请求模型
    3. 如果模型要调用工具，就执行工具
    4. 把工具结果发回模型
    5. 直到模型不再调用工具，输出最终回答
    """
    start_time = time.time()

    messages = [
        {
            "role": "system",
            "content": """
你是一个会使用工具的 Python Agent。

你有两个工具：
1. calculator：用于数学计算。
2. fake_search：用于模拟搜索资料、解释概念、查询背景信息。

规则：
1. 能直接回答的问题，可以直接回答。
2. 遇到明确数学计算，优先调用 calculator。
3. 遇到搜索、查询、查资料、了解概念，优先调用 fake_search。
4. 拿到工具结果后，要给用户一个清楚的最终答案。
"""
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    for step in range(max_steps):
        if time.time() - start_time > timeout_seconds:
            return "任务超时，Agent 已停止。"

        print(f"\n===== Agent Step {step + 1} =====")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )

        assistant_message = response.choices[0].message

        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        tool_calls = assistant_message.tool_calls

        if not tool_calls:
            return assistant_message.content

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments

            print("模型请求调用工具：", tool_name)
            print("模型生成的原始参数：", raw_arguments)

            try:
                tool_args = json.loads(raw_arguments)
                result = call_function(tool_name, tool_args)

                tool_result = {
                    "ok": True,
                    "result": result
                }

            except Exception as e:
                tool_result = {
                    "ok": False,
                    "error": type(e).__name__,
                    "detail": str(e)
                }

            print("Python 工具执行结果：", tool_result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                }
            )

    return "达到最大步数限制，Agent 已停止。"


if __name__ == "__main__":
    print("Minimal Qwen Agent 已启动。输入 exit 退出。")

    while True:
        user_text = input("\n你：")

        if user_text.lower() in ["exit", "quit"]:
            break

        answer = run_agent(user_text)

        print("\nAgent：")
        print(answer)