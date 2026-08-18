# RepoMind Demo Script

## 1. Demo Goal

这次演示的目标是展示 RepoMind 作为“AI 开源项目学习助手”的当前 Learning MVP 能力。

演示重点：

- Learning Map：索引后自动给出项目学习入口和 starter questions。
- Guided Q&A：围绕项目概览、功能实现、AI 概念、配置问题生成结构化回答。
- Source Evidence：回答带 `[Source N]` 证据，右侧可查看文件、符号、行号、source role、relevance reason。
- Refusal：当仓库证据不足时，回答应明确拒答或说明证据不足。

本演示只展示当前已经实现的能力，不展示代码编辑、MCP、多语言 AST、完整 call graph 或 local LLM。

## 2. Demo Repository

主演示仓库：`nanoGPT`

选择原因：

- 它是典型 AI 开源项目，包含模型、训练、采样、配置和数据准备代码。
- 仓库规模适合快速索引和解释。
- 当前评测资产已经围绕 nanoGPT 建立，问题覆盖 overview、feature、concept、configuration 和 negative/refusal。

## 3. Demo Setup

演示前准备：

- 本机已有 RepoMind 项目。
- 已有一个本地 nanoGPT 仓库路径。
- 依赖已按 README 安装。
- `.env` 中已配置 `DEEPSEEK_API_KEY`。
- 使用当前 README 中的启动方式运行：

```bash
streamlit run app.py
```

不要在演示中承诺未验证的新安装流程或额外环境能力。

## 4. Demo Flow

### Step 1: 输入本地 repo 路径

在左侧 Repository 面板输入本地 nanoGPT 仓库路径。

讲解要点：

- RepoMind 当前面向单仓库学习。
- 当前只加载 Python 和 Markdown 文件。

### Step 2: 点击索引

点击 **Index repository**。

讲解要点：

- 索引流程会读取文件、切分 chunk、生成 Jina embeddings，并保存到 Chroma。
- Python 使用 AST-aware chunking，Markdown 使用 fixed chunking。
- 检索层仍然使用 Chroma vector search、BM25、RRF 和 dedup。

### Step 3: 展示 Learning Map

索引成功后，在 chat 区域顶部展示 Learning Map。

讲解要点：

- Learning Map 是给初学者的第一张学习路线图。
- 它用于回答“这个项目做什么”“从哪里开始读”“有哪些主要模块”。
- 如果 Learning Map 生成失败，索引仍然可用，聊天仍可继续。

### Step 4: 点击一个 starter question

点击 Learning Map 中的一个 starter question，让它进入同一个问答流程。

讲解要点：

- starter question 不是独立功能路径，它会走和手动提问相同的 `ask()` 流程。
- 这让用户可以从 Learning Map 自然进入 Guided Q&A。

### Step 5: 提一个 feature 问题

输入 feature 问题，例如：

```text
How is self-attention implemented?
```

讲解要点：

- Guided Q&A 会识别这是功能实现类问题。
- 回答应包含实现相关结构化 section。
- Source Inspector 应能看到 `model.py` 和相关 attention 符号证据。

### Step 6: 提一个 concept 问题

输入 concept 问题，例如：

```text
What does attention mask do in this codebase?
```

讲解要点：

- 这个回答应区分通用概念和仓库里的具体实现。
- 好的回答应该解释它在 nanoGPT 代码中出现在哪里，以及输入输出或行为上的作用。

### Step 7: 提一个 negative/refusal 问题

输入 negative 问题，例如：

```text
How does nanoGPT perform reinforcement learning from human feedback?
```

讲解要点：

- 这个问题用于验证 refusal。
- 如果检索到了 README 或训练代码，也不能把普通训练流程说成 RLHF。
- 正确行为是明确说明仓库证据不足或没有相关实现。

### Step 8: 查看 Source Inspector

点击回答下方的 **Source 1** / **Source 2** 按钮。

讲解要点：

- Source Inspector 展示文件、符号、行号和源码片段。
- 当前还会显示 `source_role` 和 `relevance_reason`。
- 这说明回答不是只给自然语言总结，而是可以追溯到具体代码证据。

### Step 9: 展开 Retrieval Debug

在 Sources 面板里展开 **Retrieval details**。

讲解要点：

- 可以看到 vector、BM25、RRF 的排名和分数。
- 这是为了让检索失败或误召回可检查。
- 对学习工具来说，透明证据链比只给一个答案更重要。

## 5. Exact Demo Questions

优先使用当前 nanoGPT Learning eval dataset 中的问题。

Starter question 示例：

```text
Which files should I read first to understand nanoGPT?
```

Feature 问题：

```text
How is self-attention implemented?
```

Concept 问题：

```text
What does attention mask do in this codebase?
```

Negative/refusal 问题：

```text
How does nanoGPT perform reinforcement learning from human feedback?
```

可选备用问题：

```text
How does text generation work?
```

```text
How are configuration values overridden?
```

```text
Where is the vision transformer model defined?
```

## 6. What To Point Out During Demo

Learning Map 为什么有用：

- 初学者不需要先猜入口文件。
- 它把项目目的、主要模块、阅读顺序和 starter questions 放在索引后第一屏。
- 它是学习辅助，不是完整架构证明。

回答为什么是 source-grounded：

- 回答要求使用 `[Source N]` 引用仓库事实。
- Source Inspector 能打开对应文件、符号、行号和源码片段。
- Retrieval Debug 能查看这些 sources 是如何被检索出来的。

follow-up 怎么继续学习：

- 每条 assistant answer 下方会给出 3 个 follow-up。
- 点击 follow-up 会走同一个 Guided Q&A 流程。
- 这让学习过程从一次性问答变成连续阅读路径。

refusal 为什么重要：

- AI 项目里常有相似概念，但仓库未必实现。
- 比如 nanoGPT 有训练和采样，但不代表它实现 RLHF 或 beam search。
- 正确拒答比编造不存在的模块更重要。

## 7. Known Limitations To Say Out Loud

演示时应主动说明：

- 当前只支持 Python / Markdown。
- Python 有 AST-aware chunking，其他语言没有 multi-language AST。
- Symbol-level retrieval 仍可能弱于 file-level retrieval。
- RepoMind 不支持代码编辑。
- RepoMind 不支持 MCP。
- RepoMind 不支持完整 call graph。
- RepoMind 不支持 local LLM。
- 当前仍以 single-repo learning 为主。
- Learning Map 是 grounded learning aid，不是完整架构证明。

## 8. Demo Success Criteria

一次成功演示至少应看到：

- nanoGPT 索引成功。
- Learning Map 出现在 chat 区域顶部。
- starter question 可以点击并进入问答。
- feature answer 有结构化 section，并引用 `[Source N]`。
- concept answer 能区分概念解释和仓库实现。
- negative question 明确拒答或说明证据不足。
- Sources 可点击检查。
- Source Inspector 显示文件、符号、行号、source role 和 relevance reason。
- Retrieval Debug 可展开并显示 vector / BM25 / RRF 信息。
