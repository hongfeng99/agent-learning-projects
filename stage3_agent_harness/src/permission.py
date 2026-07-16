def request_permission(
    tool_name: str,
    arguments: dict,
) -> bool:
    """
    在危险工具执行前请求用户授权。

    返回：
    True  -> 用户允许执行
    False -> 用户拒绝执行
    """

    print("\n检测到危险工具")
    print("=" * 50)
    print(f"工具名称：{tool_name}")
    print(f"工具参数：{arguments}")

    while True:
        answer = input(
            "是否允许执行该工具？[y/n]："
        ).strip().lower()

        if answer in {"y", "yes"}:
            print("用户已授权执行。")
            return True

        if answer in {"n", "no"}:
            print("用户已拒绝执行。")
            return False

        print("请输入 y 或 n。")