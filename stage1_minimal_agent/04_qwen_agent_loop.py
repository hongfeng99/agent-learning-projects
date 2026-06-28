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


def call_function(name: str, args: dict):
    """
    工具路由函数。
    模型只会告诉我们要调用哪个工具，真正执行工具的是 Python。
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
规则：
1. 能直接回答的问题，可以直接回答。
2. 遇到数学计算，优先调用 calculator 工具。
3. 拿到工具结果后，要给用户一个清楚的最终答案。
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