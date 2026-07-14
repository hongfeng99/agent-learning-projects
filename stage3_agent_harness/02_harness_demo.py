from src.tool_registry import get_tool, list_tool_descriptions
from src.permission import check_permission
from src.trace_logger import TraceLogger
from src.session_store import SessionStore
from src.context_manager import compact_messages


def run_tool(tool_name: str, arguments: dict, trace: TraceLogger):
    """
    Harness 的核心：
    1. 找工具
    2. 检查权限
    3. 执行工具
    4. 记录 trace
    """
    trace.log("tool_requested", {
        "tool_name": tool_name,
        "arguments": arguments,
    })

    tool_info = get_tool(tool_name)

    allowed = check_permission(tool_name)
    trace.log("permission_checked", {
        "tool_name": tool_name,
        "allowed": allowed,
    })

    if not allowed:
        trace.log("tool_denied", {
            "tool_name": tool_name,
        })
        return "工具执行被拒绝"

    try:
        result = tool_info["function"](**arguments)

        trace.log("tool_finished", {
            "tool_name": tool_name,
            "status": "success",
            "result": result,
        })

        return result

    except Exception as e:
        trace.log("tool_finished", {
            "tool_name": tool_name,
            "status": "error",
            "error": str(e),
        })

        return f"工具执行失败: {e}"


def main():
    trace = TraceLogger()
    session = SessionStore()

    print("Stage3 Agent Harness Demo")
    print("=" * 40)
    print("当前可用工具：")
    print(list_tool_descriptions())
    print("=" * 40)

    # 模拟一个 agent 任务：先列文件，再总结 note.txt，再写 summary.txt
    # 现在先不用 LLM，先手动模拟 agent 的 tool plan。
    task = "读取 note.txt，总结内容，并保存到 summary.txt"
    print(f"任务：{task}")

    session.add_message("user", task)

    result1 = run_tool(
        "list_files",
        {},
        trace
    )
    print("\n[list_files 结果]")
    print(result1)
    session.add_message("tool", result1)

    result2 = run_tool(
        "summarize_file",
        {"filename": "note.txt"},
        trace
    )
    print("\n[summarize_file 结果]")
    print(result2)
    session.add_message("tool", result2)

    result3 = run_tool(
        "write_file",
        {
            "filename": "summary.txt",
            "content": result2,
        },
        trace
    )
    print("\n[write_file 结果]")
    print(result3)
    session.add_message("tool", result3)

    compacted = compact_messages(session.data["messages"])
    print("\n[压缩后的上下文]")
    for msg in compacted:
        print(f"{msg['role']}: {msg['content']}")

    print("\n运行结束。")
    print("请查看：")
    print("- demo_workspace/summary.txt")
    print("- traces/trace_demo.jsonl")
    print("- sessions/session_demo.json")


if __name__ == "__main__":
    main()