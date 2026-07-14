# Stage3 学习笔记：参考 hello-agents 复现 Agent Harness

## 参考项目

本阶段参考 Datawhale 的 hello-agents 项目，重点不是完整复制所有章节，而是学习其中“自研 Agent 框架”的思想。

## 我重点关注的内容

1. Agent loop：智能体如何循环执行任务
2. Tool registry：工具如何注册和统一调用
3. Permission gate：危险动作如何加权限控制
4. Session store：会话状态如何保存
5. Trace logger：每一步执行过程如何记录
6. Context compaction：上下文过长时如何压缩

## 为什么不完整复现 hello-agents

hello-agents 是一个完整教程，覆盖 ReAct、低代码平台、框架实践、Memory、RAG、上下文工程、协议、多智能体、DeepResearch 等内容。

Stage3 的目标更聚焦：研究一个现代 Agent Harness，并实现一个可调试 demo。

## 本阶段最终目标

实现一个最小 Agent Harness：

- 可以注册工具
- 可以执行工具
- 可以区分安全工具和危险工具
- 危险工具需要人工确认
- 可以保存 session
- 可以记录 trace
- 可以做简单上下文压缩