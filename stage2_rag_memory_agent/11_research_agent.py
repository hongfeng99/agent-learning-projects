import os
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient

from src.llm_client import chat


load_dotenv()


def get_tavily_client() -> TavilyClient:
    """
    创建 Tavily 客户端。
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError(
            "没有找到 TAVILY_API_KEY。请检查项目根目录的 .env 文件。"
        )

    return TavilyClient(api_key=api_key)


def tavily_search_tool(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    工具 1：调用 Tavily 搜索。

    输入：
        query: 用户想研究的主题
        max_results: 最多返回多少条搜索结果

    输出：
        包含 title、url、content 的搜索结果列表
    """
    client = get_tavily_client()

    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
    except Exception as e:
        raise RuntimeError(f"Tavily 搜索失败：{e}") from e

    results = response.get("results", [])

    cleaned_results = []

    for item in results:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        content = item.get("content", "").strip()

        if not url:
            continue

        cleaned_results.append(
            {
                "title": title or "无标题",
                "url": url,
                "content": content or "无摘要",
            }
        )

    return cleaned_results


def build_research_context(results: list[dict[str, Any]]) -> str:
    """
    把搜索结果整理成给大模型看的上下文。
    """
    context_parts = []

    for i, item in enumerate(results, start=1):
        context_parts.append(
            f"[{i}] 标题：{item['title']}\n"
            f"链接：{item['url']}\n"
            f"摘要：{item['content']}"
        )

    return "\n\n".join(context_parts)


def build_research_sources(results: list[dict[str, Any]]) -> str:
    """
    构建最终展示给用户的引用链接列表。
    """
    source_lines = []

    for i, item in enumerate(results, start=1):
        source_lines.append(
            f"[{i}] {item['title']}\n"
            f"    {item['url']}"
        )

    return "\n".join(source_lines)


def research_answer(topic: str, max_results: int = 5) -> str:
    """
    资料研究助手主函数。

    输入主题：
        调用搜索工具
        整理搜索结果
        调用大模型总结
        输出引用来源
    """
    if not topic.strip():
        return "请输入一个有效的研究主题。"

    try:
        results = tavily_search_tool(topic, max_results=max_results)
    except Exception as e:
        return f"搜索工具调用失败，无法完成研究。\n错误信息：{e}"

    if not results:
        return "没有搜索到足够相关的资料，无法生成可靠总结。"

    context = build_research_context(results)
    sources = build_research_sources(results)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个严谨的资料研究助手。"
                "你只能根据提供的搜索结果进行总结。"
                "不要编造搜索结果中不存在的事实。"
                "回答关键结论时必须使用 [1]、[2] 这样的引用编号。"
                "如果搜索结果不足，就明确说明资料不足。"
            ),
        },
        {
            "role": "user",
            "content": f"""
用户研究主题：

{topic}

下面是搜索工具返回的资料：

{context}

请完成一个简洁的资料研究总结。

要求：
1. 先用 3-5 条要点总结核心信息。
2. 每个关键结论后面尽量标注引用编号，例如 [1]。
3. 不要使用搜索结果以外的信息。
4. 如果资料不足，请明确说明。
""",
        },
    ]

    answer = chat(messages)

    return f"{answer}\n\n引用来源：\n{sources}"


def main() -> None:
    print("Research Agent 已启动。")
    print("输入一个研究主题，我会搜索、筛选、总结并输出引用链接。")
    print("输入 exit 退出。")

    while True:
        topic = input("\n请输入研究主题：").strip()

        if topic.lower() in ["exit", "quit", "q"]:
            print("退出。")
            break

        if not topic:
            continue

        answer = research_answer(topic)

        print("\n===== 研究结果 =====")
        print(answer)


if __name__ == "__main__":
    main()