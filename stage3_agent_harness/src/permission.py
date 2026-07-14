from src.tool_registry import get_tool


def check_permission(tool_name: str) -> bool:
    """
    简单权限控制：
    - 非危险工具直接允许
    - 危险工具需要用户手动确认
    """
    tool_info = get_tool(tool_name)

    if not tool_info["dangerous"]:
        return True

    print(f"\n工具 {tool_name} 被标记为危险工具。")
    answer = input("是否允许执行？输入 y 允许，其他内容拒绝：").strip().lower()

    return answer == "y"