def compact_messages(messages: list, max_messages: int = 6) -> list:
    """
    最简单的上下文压缩：
    如果消息太多，就把早期消息压缩成一条 summary。
    """
    if len(messages) <= max_messages:
        return messages

    old_messages = messages[:-max_messages]
    recent_messages = messages[-max_messages:]

    summary_text = "早期对话摘要："

    for msg in old_messages:
        summary_text += f"\n{msg['role']}: {msg['content'][:80]}"

    compacted = [
        {
            "role": "system",
            "content": summary_text,
        }
    ]

    return compacted + recent_messages