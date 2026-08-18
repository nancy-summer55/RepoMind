# RepoMind User Guide

## 1. RepoMind 适合谁用

RepoMind 适合正在学习 AI 开源项目、但还不熟悉项目结构和源码入口的用户。

它更适合这些场景：

- 第一次阅读一个 AI 代码仓库，不知道先看哪些文件。
- 想理解一个功能是如何在源码中实现的。
- 想把 AI 概念和真实仓库代码对应起来。
- 想检查回答背后的源码证据，而不是只看自然语言总结。
- 想用 follow-up questions 连续深入学习一个项目。

RepoMind 当前不是代码编辑器，也不是自动改代码工具。它的重点是源码理解、学习路径和 source-grounded Q&A。

## 2. 启动前准备

启动前需要准备：

- 本机已有 RepoMind 项目。
- 已安装 README 中列出的依赖。
- 已准备一个本地 Python / Markdown 仓库路径。
- `.env` 中已配置 `DEEPSEEK_API_KEY`。

启动方式沿用 README：

```bash
streamlit run app.py
```

当前生成回答和 Learning Map 使用 DeepSeek，因此网络和 API 可用性会影响生成结果。

## 3. 如何索引本地仓库

1. 打开 RepoMind 页面。
2. 在左侧 Repository 面板输入本地仓库路径。
3. 点击 **Index repository**。
4. 等待索引完成。

索引成功后，左侧会显示仓库名称、文件数、chunk 数、chunking 策略和 embedding 信息。

当前索引行为：

- 只加载 `.py` 和 `.md` 文件。
- Python 文件使用 AST-aware chunking。
- Markdown 文件使用 fixed chunking。
- embedding 使用 Jina code embeddings。
- 索引保存到 Chroma。
- 重新索引会重建当前 Chroma collection，并清空上一轮聊天状态。

## 4. 如何阅读 Learning Map

索引成功后，chat 区域顶部会显示 Learning Map。

你可以优先看这些内容：

- 项目摘要：先判断这个仓库大致做什么。
- 入口点或推荐阅读顺序：决定第一批要读的文件。
- 主要模块：理解项目大块职责。
- starter questions：直接点击进入问答。

Learning Map 是学习辅助，不是完整架构证明。它基于仓库文档、文件 profile、chunk metadata 和选中的 source evidence 生成。如果证据不足，回答或 Learning Map 应说明不确定性。

如果 Learning Map 生成失败，仓库索引仍然可用，你仍然可以在 chat 中提问。

## 5. 如何提 feature / concept / configuration 问题

RepoMind 当前支持 Guided Q&A，会根据问题类型生成不同回答结构。

Feature 问题适合问“功能如何实现”：

```text
How is self-attention implemented?
```

```text
How does text generation work?
```

Concept 问题适合问“AI 概念在代码中如何体现”：

```text
What does attention mask do in this codebase?
```

```text
How are logits and loss computed in a forward pass?
```

Configuration 问题适合问“配置在哪里定义、读取或覆盖”：

```text
How are configuration values overridden?
```

```text
How is the training device chosen?
```

回答应尽量引用 `[Source N]`。如果仓库证据不足，应该明确说明，而不是编造文件、类、函数、配置或运行行为。

## 6. 如何使用 starter questions 和 follow-ups

starter questions 出现在 Learning Map 中，适合刚索引完仓库时使用。

推荐用法：

1. 先点击一个 starter question。
2. 阅读回答中的结构化 section。
3. 查看回答下方的 3 个 follow-up questions。
4. 点击一个 follow-up 继续深入。

follow-up 点击后会走和手动提问相同的 `ask()` 流程。它不是单独的快捷回复，而是一次新的 Guided Q&A。

## 7. 如何查看 Source Inspector 和 Retrieval Debug

每条 assistant answer 下方可能会显示 **Source 1**、**Source 2** 等按钮。

点击 source 按钮后，右侧 Source Inspector 会显示：

- source 编号
- 文件路径
- 符号或 qualified name
- 行号范围
- source role
- relevance reason
- 源码片段

Source Inspector 用来检查回答是否真的有代码证据支持。

在 Sources 面板中展开 **Retrieval details** 可以查看：

- Final Rank
- Vector Rank / Vector Similarity
- BM25 Rank / BM25 Score
- RRF Rank / RRF Score
- Chunk Strategy
- Symbol
- Lines

Retrieval Debug 用来判断检索是否命中正确文件和符号，也方便分析回答失败是否来自 retrieval miss。

## 8. 遇到 refusal / insufficient context 时怎么看

当问题超出仓库证据范围时，RepoMind 应该拒答或说明证据不足。

例如：

```text
How does nanoGPT perform reinforcement learning from human feedback?
```

如果仓库没有 RLHF 实现，正确行为不是猜测或泛泛解释 RLHF，而是说明 retrieved sources 中没有相关实现。

遇到 refusal 时建议检查：

- Sources 是否只是相似但不真正相关。
- Retrieval Debug 中 Top-K 是否命中了预期文件。
- 回答是否明确说明缺少证据。
- 是否需要把问题改得更贴近仓库已有文件或符号。

Refusal 是有价值的行为，因为它降低了把不存在功能说成已实现的风险。

## 9. 当前限制

当前应明确知道这些限制：

- 只支持 Python / Markdown 文件。
- 只有 Python 支持 AST-aware chunking。
- 不支持 multi-language AST。
- 不支持完整 call graph。
- 不支持代码编辑。
- 不支持 MCP。
- 不支持 local LLM。
- 仍以单仓库学习为主。
- 重新索引会重建当前 Chroma collection。
- BM25 当前按查询从 Chroma collection 构建。
- DeepSeek 调用依赖网络和 API 可用性。
- symbol-level retrieval 仍可能弱于 file-level retrieval。
- Learning Map 是 grounded learning aid，不是完整架构证明。

## 10. 建议提问示例

Overview：

```text
What does this project do?
```

```text
Which files should I read first to understand nanoGPT?
```

Feature：

```text
How is self-attention implemented?
```

```text
How does text generation work?
```

Concept：

```text
What does attention mask do in this codebase?
```

```text
What is the role of the Block class in the transformer?
```

Configuration：

```text
How are configuration values overridden?
```

```text
Where are model architecture sizes defined?
```

File or symbol：

```text
Explain model.py
```

```text
What is GPT.generate?
```

Negative / refusal：

```text
How does nanoGPT perform reinforcement learning from human feedback?
```

```text
Where is the vision transformer model defined?
```
