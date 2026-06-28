import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI



# =========================
# 1. 读取 .env
# =========================

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

modelscope_api_key = os.getenv("MODELSCOPE_API_KEY")
modelscope_base_url = os.getenv("MODELSCOPE_BASE_URL")
modelscope_model = os.getenv("MODELSCOPE_MODEL")
tavily_api_key = os.getenv("TAVILY_API_KEY")
print("TAVILY_API_KEY 是否读取到：", tavily_api_key is not None)
print("TAVILY_API_KEY 前10个字符：", repr(tavily_api_key[:10]) if tavily_api_key else None)

if not modelscope_api_key:
    raise ValueError("缺少 MODELSCOPE_API_KEY，请检查 .env 文件")

if not modelscope_base_url:
    raise ValueError("缺少 MODELSCOPE_BASE_URL，请检查 .env 文件")

if not modelscope_model:
    raise ValueError("缺少 MODELSCOPE_MODEL，请检查 .env 文件")

if not tavily_api_key:
    raise ValueError("缺少 TAVILY_API_KEY，请检查 .env 文件")


# =========================
# 2. 初始化 ModelScope 客户端
# =========================

client = OpenAI(
    api_key=modelscope_api_key,
    base_url=modelscope_base_url,
)

MODEL = modelscope_model


# =========================
# 3. 初始化 Tavily 客户端
# =========================

# tavily_client = TavilyClient(api_key=tavily_api_key)
# =========================
# 4. 定义 Tavily 搜索函数
# =========================

def tavily_search(query: str) -> str:
    """
    使用 Tavily REST API 执行联网搜索。
    这个版本不用 tavily-python SDK，避免中文 query 触发 latin-1 编码问题。
    """

    try:
        url = "https://api.tavily.com/search"

        headers = {
            "Authorization": f"Bearer {tavily_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": True,
        }

        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        answer = data.get("answer", "")
        results = data.get("results", [])

        output = []

        if answer:
            output.append(f"搜索摘要：{answer}")

        for index, item in enumerate(results, start=1):
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")

            output.append(
                f"{index}. 标题：{title}\n链接：{url}\n内容：{content}"
            )

        if not output:
            return "没有搜索到相关结果。"

        return "\n\n".join(output)

    except Exception as e:
        return f"Tavily 搜索失败：{e}"

def calculator(expression: str) -> str:
    """
    简单计算器工具。
    只允许数字、括号、小数点和四则运算符，避免 eval 执行危险代码。
    """

    allowed_chars = "0123456789+-*/(). "

    for char in expression:
        if char not in allowed_chars:
            return "表达式中包含不允许的字符，无法计算。"

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算失败：{e}"
    


def read_file(filename: str) -> str:
    """
    读取 workspace 目录下的文本文件。
    为了安全，只允许读取 workspace 目录内部的文件。
    """

    workspace_dir = os.path.join(os.path.dirname(__file__), "workspace")
    file_path = os.path.join(workspace_dir, filename)

    abs_workspace = os.path.abspath(workspace_dir)
    abs_file_path = os.path.abspath(file_path)

    # 防止读取 workspace 之外的文件，例如 ../../.env
    if os.path.commonpath([abs_workspace, abs_file_path]) != abs_workspace:
        return "不允许读取 workspace 目录之外的文件。"

    if not os.path.exists(abs_file_path):
        return f"文件不存在：{filename}"

    try:
        with open(abs_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return f"{filename} 文件是空的。"

        return content

    except Exception as e:
        return f"读取文件失败：{e}"

# =========================
# 5. 定义 tools，给模型看
# =========================

tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "当用户的问题需要最新信息、实时信息、新闻、外部资料、联网查询时，调用这个搜索工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要搜索的问题或关键词",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "当用户的问题需要数学计算时，调用这个计算器工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 23 * 45 + 78",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "当用户要求读取 workspace 目录下的本地文本文件时，调用这个文件读取工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "要读取的文件名，例如 note.txt",
                    }
                },
                "required": ["filename"],
            },
        },
    },
]


# =========================
# 6. 工具分发函数
# =========================

def call_function(name: str, arguments: dict) -> str:
    """
    根据模型生成的 tool_call，分发到不同的 Python 函数。
    """

    if name == "search":
        return tavily_search(arguments["query"])

    elif name == "calculator":
        return calculator(arguments["expression"])

    elif name == "read_file":
        return read_file(arguments["filename"])

    else:
        return f"未知工具：{name}"
# =========================
# 7. Agent 主流程
# =========================

def run_agent(user_input: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个可以使用工具的 Agent。"
                "当问题需要最新信息或外部资料时，调用 search 工具；"
                "当问题需要数学计算时，调用 calculator 工具；"
                "当用户要求读取 workspace 目录下的文件时，调用 read_file 工具。"
                "工具返回结果后，请基于工具结果直接给出最终回答，不要重复调用同一个工具。"
            ),
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    max_rounds = 5

    for round_index in range(max_rounds):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # 如果模型没有调用工具，说明可以直接回答
        if not assistant_message.tool_calls:
            if assistant_message.content:
                return assistant_message.content
            else:
                return "模型没有返回有效内容。"

        # 如果模型调用了工具，把 assistant 的 tool_call 消息加入 messages
        messages.append(assistant_message)

        # 执行模型要求调用的所有工具
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print("\n模型决定调用工具：")
            print("工具名：", function_name)
            print("参数：", function_args)

            function_result = call_function(function_name, function_args)

            print("\n工具执行结果：")
            print(function_result[:500])
            print("...")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_result,
                }
            )

    return "工具调用轮次过多，已停止。"


# =========================
# 8. 命令行入口
# =========================

if __name__ == "__main__":
    print("Qwen Final Agent 已启动")
    print("已支持工具：search / calculator / read_file")
    print("输入 exit / quit / q 可以退出")

    while True:
        user_input = input("\n你：")

        if user_input.lower() in ["exit", "quit", "q"]:
            print("已退出")
            break

        answer = run_agent(user_input)

        print("\nAgent：")
        print(answer)