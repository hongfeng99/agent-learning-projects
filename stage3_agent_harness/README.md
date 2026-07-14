# Stage3 Agent Harness

本阶段参考 Datawhale hello-agents 项目，复现一个最小 Agent Harness。

## 学习目标

- 理解 agent loop
- 理解 tool registry
- 理解 permission gate
- 理解 session store
- 理解 trace logger
- 理解 context compaction

## 当前实现

本 demo 暂时不接 LLM，而是手动模拟 agent 的工具调用计划：

1. list_files
2. summarize_file
3. write_file

Harness 负责：

1. 查找工具
2. 检查权限
3. 执行工具
4. 记录 trace
5. 保存 session

## 运行方式

```bash
python 02_harness_demo.py