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


# =========================
# 5. 定义 tools，给模型看
# =========================

tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "当用户的问题需要最新信息、实时信息、新闻、资料查询、联网搜索时，调用这个搜索工具。",
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
    }
]


# =========================
# 6. 工具分发函数
# =========================

def call_function(name: str, arguments: dict) -> str:
    """
    根据模型要求调用对应的 Python 函数。
    """

    if name == "search":
        return tavily_search(arguments["query"])

    return f"未知工具：{name}"


# =========================
# 7. Agent 主流程
# =========================

def run_agent(user_input: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "你是一个可以使用搜索工具的 Agent。当问题需要最新信息或外部资料时，应该调用 search 工具。",
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    # 第一次请求模型：让模型判断是否需要调用工具
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    # 如果模型没有调用工具，直接返回回答
    if not assistant_message.tool_calls:
        return assistant_message.content

    # 把 assistant 的 tool_call 消息加入 messages
    messages.append(assistant_message)

    # 执行所有工具调用
    for tool_call in assistant_message.tool_calls:
        function_name = tool_call.function.name

        # tool_call.function.arguments 是 JSON 字符串
        function_args = json.loads(tool_call.function.arguments)

        print("\n模型决定调用工具：")
        print("工具名：", function_name)
        print("参数：", function_args)

        # Python 真正执行工具
        function_result = call_function(function_name, function_args)

        print("\n工具执行结果：")
        print(function_result[:500])
        print("...")

        # 把工具结果返回给模型
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_result,
            }
        )

    # 第二次请求模型：让模型根据工具结果生成最终回答
    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    return final_response.choices[0].message.content


# =========================
# 8. 命令行入口
# =========================

if __name__ == "__main__":
    print("Qwen + Tavily Search Agent 已启动")
    print("输入 exit / quit / q 可以退出")

    while True:
        user_input = input("\n你：")

        if user_input.lower() in ["exit", "quit", "q"]:
            print("已退出")
            break

        answer = run_agent(user_input)

        print("\nAgent：")
        print(answer)