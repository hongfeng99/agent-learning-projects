from src.session_store import SessionStore


def main():
    # 不传 session_id，自动创建新会话
    session = SessionStore()

    print("Session ID：")
    print(session.session_id)

    print("\nSession 文件：")
    print(session.path)

    session.add_message(
        {
            "role": "system",
            "content": "你是一个测试助手。",
        }
    )

    session.add_message(
        {
            "role": "user",
            "content": "测试会话保存。",
        }
    )

    session.add_message(
        {
            "role": "assistant",
            "content": "会话保存成功。",
        }
    )

    print("\n消息数量：")
    print(len(session.messages))

    print("\n当前消息：")
    for message in session.messages:
        print(message)

    # 使用相同 ID 再创建 SessionStore，
    # 它应该加载刚才的历史记录
    loaded_session = SessionStore(
        session_id=session.session_id
    )

    print("\n重新加载后的消息数量：")
    print(len(loaded_session.messages))


if __name__ == "__main__":
    main()