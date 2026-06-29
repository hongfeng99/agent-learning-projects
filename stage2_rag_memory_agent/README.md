\# Stage2: RAG + Memory Agent



本阶段目标：实现一个具备 RAG 检索能力和长期记忆能力的简单 Agent。



\## 目录说明



\- `01\_load\_document.py`：读取本地文档

\- `02\_chunk\_document.py`：将文档切分成 chunks

\- `03\_retrieve\_baseline.py`：基于简单字符匹配进行检索

\- `04\_rag\_answer.py`：实现基础 RAG 问答

\- `05\_modular\_rag.py`：将 RAG 流程模块化

\- `06\_memory\_agent.py`：实现长期记忆 Agent

\- `07\_memory\_rag\_agent.py`：整合 RAG 和 Memory

- `08_embedding_retriever.py`：使用 embedding 相似度进行语义检索
- `09_rag_with_citations.py`：基于 embedding 检索生成带引用来源的 RAG 回答
- `10_toolified_rag_agent.py`：将 RAG 和 Memory 包装成工具，由 Agent 选择调用

- `13_guarded_research_agent.py`：在 Research Agent 基础上增加工具失败、空结果、重复调用和幻觉引用检查。
\## 核心流程



用户输入问题后：



1\. 读取长期记忆 `memory/memory.json`

2\. 读取本地文档 `data/raw/sample.txt`

3\. 将文档切分为 chunks

4\. 根据问题检索相关 chunks

5\. 构建 prompt

6\. 调用大模型回答

7\. 必要时保存长期记忆



\## 运行方式



先进入 Stage2 目录：



```bash

cd stage2\_rag\_memory\_agent

