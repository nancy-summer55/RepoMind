# RepoMind 产品汇报

## 1. 产品一句话定义

RepoMind 是一个面向 AI 初学者的开源源码学习助手。它不是通用代码聊天工具，而是帮助用户从本地代码仓库中快速建立学习路径、理解功能实现，并把 AI 概念和真实代码对应起来。

## 2. 用户洞察

### 2.1 用户是谁

RepoMind 当前主要面向：

- 有基础 Python 阅读能力的 AI 初学者
- 希望通过真实开源项目学习 AI 工程实现的开发者
- 需要快速理解项目结构、模块关系和实现路径的人

### 2.2 我们洞察到的核心问题

围绕目标用户，RepoMind 识别出四个高频、连续出现的真实需求：

1. 用户打开一个 AI 开源仓库后，不知道从哪里开始读。
2. 用户能提问题，但不知道哪些文件、模块、函数真正重要。
3. 用户能拿到 LLM 回答，但无法确认这个回答是不是基于仓库真实代码。
4. 用户想把 AI 概念和仓库实现对应起来，但通用回答通常停留在教材层，不落到代码。

这些问题说明，用户缺的不只是“搜索能力”，而是：

- 学习路径
- 源码证据
- 引导式提问
- 对错误答案的防护

## 3. 产品目标

基于上述洞察，RepoMind 的 MVP 目标不是做一个更强的代码聊天产品，而是完成三件更聚焦的事：

1. 帮用户快速看懂项目全貌。
2. 帮用户理解某个功能是如何在仓库中实现的。
3. 帮用户把 AI 概念和仓库中的真实代码实现联系起来。

因此，产品从一开始就强调：

- 学习优先，而不是聊天优先
- Grounded source evidence，而不是泛泛解释
- Guided flow，而不是空白输入框

## 4. 功能设计与目标映射

### 4.1 Learning Map

为了解决“我不知道从哪里开始读”，设计了 Learning Map。

它在仓库索引后自动生成，并输出：

- 项目摘要
- 入口文件
- 主模块
- 核心流程
- 推荐阅读顺序
- starter questions

目标是让用户在第一次提问前就获得一个结构化学习入口。

### 4.2 Guided Q&A

为了解决“我想知道一个功能是怎么实现的”，设计了 Guided Q&A。

它不是直接把用户问题丢给通用 RAG，而是先做问题分类，再按问题类型组织回答。

支持的核心问答模式包括：

- feature implementation
- AI concept explanation
- project overview
- configuration / runtime behavior
- refusal / insufficient context

目标是让回答更符合学习场景，而不是停留在泛泛问答。

### 4.3 Source Evidence

为了解决“我不确定回答是否可信”，设计了 Source Evidence。

每个回答都带 source citation，并允许用户查看：

- 文件路径
- 行号
- symbol
- source role
- relevance reason
- retrieval debug

目标是把“可验证性”做成产品的一部分，而不是隐含能力。

### 4.4 Starter Questions 与 Follow-ups

为了解决“我不知道下一步该问什么”，设计了两层引导：

- Learning Map 上的 starter questions
- 每个回答后的 3 个 follow-up questions

目标是把“继续学习”变成一个自然连续的体验，而不是用户自己重新想问题。

### 4.5 Refusal / Insufficient Context

为了解决“模型可能会编”，设计了 refusal 机制。

当仓库证据不足时，系统明确拒答，而不是制造貌似流畅但不可靠的解释。

目标是保护学习可信度。

## 5. 产品完整流程

RepoMind 当前的核心体验分成两条链路。

### 5.1 学习启动链

用户进入产品后的第一条主路径是：

1. 输入本地仓库路径
2. 系统加载 `.py` 与 `.md` 文件
3. Python 使用 AST-aware chunking，Markdown 使用固定切块
4. 构建 embedding 并写入 Chroma
5. 分析文件画像与项目结构
6. 选取关键证据源
7. 生成 Learning Map
8. 展示项目摘要和 starter questions

这条链路解决的是“从哪开始学”。

### 5.2 引导式问答链

用户点击 starter question 或手动提问后，会进入第二条主路径：

1. 分类问题意图
2. 为不同意图构建 query plan
3. 使用 hybrid retrieval 获取候选源码
4. 对 source 做 role labeling
5. 生成结构化 answer prompt
6. 调用模型生成回答
7. 生成固定 3 个 follow-up questions
8. 展示 answer、sources、follow-ups、retrieval debug

这条链路解决的是“如何深入理解实现与概念”。

### 5.3 当前产品体验闭环

当前产品希望形成的学习闭环是：

`Learning Map -> Starter Question -> Structured Answer -> Follow-up -> Source Audit`

这也是 RepoMind 与通用代码问答工具最核心的差异。

## 6. 当前功能背后的技术路径

当前 MVP 沿用现有技术栈，并在其上增加学习层：

- Streamlit：交互界面
- Chroma：向量存储
- Jina embeddings：语义表示
- BM25：词法检索
- RRF：混合排序
- DeepSeek：回答与 Learning Map 生成

技术上的关键设计不是“推倒重来”，而是：

- 保留现有 RAG 基础
- 在其上叠加 learning layer
- 用 prompt、metadata、source role 和 UI 引导把产品从“搜索 demo”改造成“学习助手”

## 7. 产品目标如何转化为数据指标

RepoMind 不能只用传统检索指标来衡量，因为它不是单纯搜索工具，而是学习产品。

因此，指标设计分成三层。

### 7.1 产品结果指标

衡量产品是否真的在帮助用户开始学习：

- 首次获得可用 Learning Map 的时间
- 成功生成 Learning Map 的仓库比例
- 回答中包含 source citation 的比例
- 首答后继续提问或点击 follow-up 的比例

这层指标回答的问题是：

- 产品有没有快速给用户价值
- 用户是否愿意继续学下去

### 7.2 学习质量指标

衡量输出内容是否真的有学习价值：

- Learning Map 是否识别出至少 3 个有用模块或关键文件
- feature answer 是否具有完整结构
- concept answer 是否区分通用概念与仓库实现
- refusal 是否能在证据不足时触发

这层指标回答的问题是：

- 产品是不是一个合格的学习工具

### 7.3 检索与 groundedness 指标

衡量底层检索和回答的可信性：

- File Hit@5
- Symbol Hit@5
- Source Coverage
- Negative question 的正确拒答率
- Learning usefulness score
- Follow-up relevance score

这层指标回答的问题是：

- 系统是不是找到了正确证据
- 回答是否真实依赖这些证据

## 8. 指标如何驱动产品迭代

RepoMind 的指标不是为了展示报表，而是为了把问题准确定位到正确层级。

### 8.1 如果 Learning Map usefulness 低

说明首页没有解决“从哪开始学”的问题。

这时优先动作应该是：

- 调整 project profile 生成逻辑
- 优化 evidence selection
- 改进 reading order

而不是优先去做 UI 美化。

### 8.2 如果 File Hit@5 低

说明问题主要在 retrieval，而不是回答模板。

这时应优先调整：

- query planner
- metadata enrichment
- file importance scoring
- source selection

### 8.3 如果回答有 citation，但 usefulness 低

说明回答 grounded，但不够“教学化”。

这时应优化：

- answer template
- explanation structure
- follow-up generation

### 8.4 如果 negative question 无法正确拒答

说明可信度出现高优先级风险。

这类问题必须优先修，因为它会直接伤害用户对产品的信任。

### 8.5 如果 follow-up 点击率低

说明产品虽然能回答问题，但没有形成持续学习路径。

这时应重点优化：

- starter question 质量
- follow-up relevance
- “下一步学什么”的明确性

## 9. 当前阶段判断

截至目前，RepoMind 已经从一个 repository RAG demo 进化为一个 Learning MVP。

当前已完成：

- Learning Map
- Guided Q&A
- Source Evidence
- Refusal 机制
- 评测资产
- Demo / 使用 / 开发 / Release 文档

当前尚未完全完成的部分主要是：

- live app 全链路运行条件仍依赖真实 API key 与 embedding model 来源
- 更完整的本地运行稳定性与交互细节仍可继续优化

## 10. 下一阶段迭代建议

从产品视角看，下一阶段最重要的不是继续扩新功能，而是把当前闭环跑稳。

优先级建议如下：

1. 完成 live flow 验收：索引、Learning Map、starter question、feature、concept、refusal 全链路跑通
2. 优化运行前依赖提示：让首次启动更低摩擦
3. 根据评测结果优化 retrieval 与 prompt
4. 在运行稳定后，再考虑：
   - BM25-only fallback
   - local model path 完善
   - 更强的 symbol-level retrieval

## 11. 总结

RepoMind 的产品核心，不是在回答“这段代码是什么”，而是在回答：

**一个 AI 初学者，如何可信地学会一个开源仓库。**

这决定了它的产品设计必须围绕：

- 学习路径
- 结构化解释
- 源码证据
- 拒答机制
- 可持续追问

它不是一个更宽泛的代码助手，而是一个更具体、更适合学习场景的源码学习产品。
