from src.trace_logger import TraceLogger


def main():
    trace = TraceLogger()

    print("Trace 文件位置：")
    print(trace.path)

    trace.log(
        "run_started",
        {
            "task": "测试 TraceLogger",
        },
    )

    trace.log(
        "tool_requested",
        {
            "tool_name": "list_files",
            "arguments": {},
        },
    )

    trace.log(
        "tool_finished",
        {
            "tool_name": "list_files",
            "result": ["note.txt"],
        },
    )

    trace.log(
        "run_finished",
        {
            "status": "success",
        },
    )

    print("\n测试日志已经写入。")


if __name__ == "__main__":
    main()