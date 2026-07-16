from src.agent_runtime import run_agent


def main():
    print("Stage3 多轮 Agent Harness")
    print("=" * 50)

    session_id = input(
        "请输入 Session ID，直接回车创建新会话："
    ).strip()

    # 空字符串转换成 None
    if not session_id:
        session_id = None

    task = input("请输入任务：").strip()

    if not task:
        print("任务不能为空。")
        return

    try:
        final_answer = run_agent(
            task=task,
            session_id=session_id,
        )

        print("\nAgent 最终回答")
        print("=" * 50)
        print(final_answer)

    except Exception as error:
        print("\nAgent 运行失败")
        print("=" * 50)
        print(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    main()