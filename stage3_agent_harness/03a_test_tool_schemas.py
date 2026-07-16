import json

from src.tool_registry import get_tool_schemas


def main():
    tool_schemas = get_tool_schemas()

    print("工具数量：", len(tool_schemas))
    print("=" * 50)

    print(
        json.dumps(
            tool_schemas,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()