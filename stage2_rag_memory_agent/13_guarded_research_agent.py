import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient

from src.llm_client import chat


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


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
    搜索工具：调用 Tavily 搜索。
    """
    client = get_tavily_client()

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
        include_raw_content=False,
    )

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


def extract_citation_numbers(answer: str) -> set[int]:
    """
    从模型回答中提取引用编号。

    例如：
        RAG 是检索增强生成 [1][2]

    提取结果：
        {1, 2}
    """
    matches = re.findall(r"\[(\d+)\]", answer)

    return {int(number) for number in matches}


def validate_citations(answer: str, source_count: int) -> tuple[bool, str]:
    """
    检查模型回答中的引用编号是否合法。

    合法情况：
        来源有 [1] [2] [3]
        回答里只引用 [1] [2] [3]

    非法情况：
        来源只有 [1] [2] [3]
        回答里却出现 [4]
    """
    used_citations = extract_citation_numbers(answer)

    if not used_citations:
        return False, "模型回答中没有使用任何引用编号。"

    valid_citations = set(range(1, source_count + 1))

    invalid_citations = used_citations - valid_citations

    if invalid_citations:
        return (
            False,
            f"模型回答中出现了不存在的引用编号：{sorted(invalid_citations)}。",
        )

    return True, "引用编号校验通过。"


def research_answer_with_guards(
    topic: str,
    tool_cache: dict[str, list[dict[str, Any]]],
    max_results: int = 5,
) -> str:
    """
    带防护的资料研究助手。

    防护点：
    1. 空输入检查
    2. 工具失败处理
    3. 空结果处理
    4. 重复调用缓存
    5. 幻觉引用检查
    """
    topic = topic.strip()

    if not topic:
        return "请输入一个有效的研究主题。"

    # 1. 防止重复调用同一个搜索工具
    if topic in tool_cache:
        print("[Guard] 发现相同主题，复用上一次搜索结果，不重复调用 Tavily。")
        results = tool_cache[topic]
    else:
        print("[Tool Call] tavily_search_tool")

        try:
            results = tavily_search_tool(topic, max_results=max_results)
        except Exception as e:
            return (
                "搜索工具调用失败，无法完成研究。\n"
                f"错误信息：{e}"
            )

        tool_cache[topic] = results

    # 2. 空结果处理
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
                "只能引用提供的编号，不允许引用不存在的编号。"
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
1. 用 3-5 条要点总结核心信息。
2. 每个关键结论后面必须标注引用编号，例如 [1]。
3. 只能使用资料中出现的引用编号。
4. 不要使用搜索结果以外的信息。
5. 如果资料不足，请明确说明。
""",
        },
    ]

    answer = chat(messages)

    # 3. 幻觉引用检查
    is_valid, citation_message = validate_citations(
        answer=answer,
        source_count=len(results),
    )

    if not is_valid:
        answer = (
            f"{answer}\n\n"
            "引用检查警告：\n"
            f"{citation_message}\n"
            "请注意：上面的回答可能存在引用不完整或引用编号异常。"
        )

    return f"{answer}\n\n引用来源：\n{sources}"


def main() -> None:
    """
    启动带防护的 Research Agent。
    """
    tool_cache: dict[str, list[dict[str, Any]]] = {}

    print("Guarded Research Agent 已启动。")
    print("这个版本会处理工具失败、空结果、重复调用、幻觉引用。")
    print("输入 exit 退出。")

    while True:
        topic = input("\n请输入研究主题：").strip()

        if topic.lower() in ["exit", "quit", "q"]:
            print("退出。")
            break

        if not topic:
            continue

        answer = research_answer_with_guards(
            topic=topic,
            tool_cache=tool_cache,
        )

        print("\n===== 研究结果 =====")
        print(answer)


if __name__ == "__main__":
    main()