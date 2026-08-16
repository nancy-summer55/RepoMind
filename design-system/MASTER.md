# RepoMind UI Design System

> Version: v0.1  
> Scope: Streamlit desktop-first UI  
> Product type: AI developer tool / open-source repository learning assistant  
> Design direction: Minimal, technical, quiet, information-dense

---

## 1. Design Goals

RepoMind 的 UI 目标不是做成传统后台 Dashboard，也不是做成“聊天机器人皮肤”。

核心目标：

1. **突出代码与来源，而不是装饰。**
2. **让用户始终知道当前正在分析哪个 Repository。**
3. **让回答、Sources、Retrieval Debug 三者形成清晰的信息层级。**
4. **默认界面极简，但技术细节可以按需展开。**
5. **优先保证桌面端开发者体验。**
6. **保持 Retrieval 行为透明，可解释。**
7. **不为了视觉效果牺牲信息密度。**

---

## 2. Product Personality

RepoMind 的视觉与交互应表现为：

- 克制
- 技术感
- 安静
- 精确
- 可信
- 工具化
- 非娱乐化

避免：

- 过度拟人化
- “AI 魔法”式视觉
- 渐变背景
- 玻璃拟态
- 大面积阴影
- Bento 卡片堆叠
- 过度动画
- 大号 Hero 文案
- Dashboard KPI 风格
- 多彩状态标签
- 与功能无关的插画

---

## 3. Information Architecture

RepoMind 第一版只保留三个主要区域：

```text
┌────────────────────────────────────────────────────────────────────┐
│ RepoMind                                      nanoGPT  ● Indexed   │
├───────────────────┬───────────────────────────────┬────────────────┤
│ Repository        │ Chat                          │ Sources        │
│                   │                               │                │
│ Path              │ User                          │ model.py       │
│ [...nanoGPT]      │ How is self-attention ...     │                │
│                   │                               │ Symbol         │
│ [ Index ]         │ RepoMind                      │ CausalSelf...  │
│                   │ Self-attention is ...         │                │
│ 19 files          │                               │ Lines 49–98    │
│ 90 chunks         │ [Source 1]                    │                │
│ AST               │                               │ View source    │
│ Jina Code         │                               │                │
│                   │                               │──────────────  │
│ Settings ▾        │                               │ Retrieval ▾    │
│                   │                               │ V #1 / B #2   │
│                   │                               │ RRF #1         │
│                   │                               │                │
│                   │ Ask about this repository...  │                │
└───────────────────┴───────────────────────────────┴────────────────┘
```

### 3.1 左侧：Repository Panel

职责：

- 输入本地 Repository 路径
- 执行 Index
- 展示当前 Index 状态
- 展示当前索引配置摘要
- 提供少量高级设置入口

不承担：

- 大量日志输出
- Retrieval 结果
- Chat history

### 3.2 中间：Conversation Workspace

职责：

- 用户问题
- RepoMind 回答
- 引用编号
- Chat history
- 底部固定 Chat Input

这是页面视觉主区域。

### 3.3 右侧：Source Inspector

职责：

- Sources
- File / Symbol / Lines
- Source code preview
- Retrieval Debug
- Vector / BM25 / RRF 排名
- Chunk strategy

默认信息简洁，Debug 默认折叠。

---

## 4. Layout

### 4.1 Desktop Grid

推荐宽度比例：

```text
Repository Panel : Chat : Inspector
       22%        : 53%  : 25%
```

Streamlit 可近似使用：

```python
repo_col, chat_col, inspector_col = st.columns(
    [0.22, 0.53, 0.25],
    gap="large"
)
```

如果左侧使用 `st.sidebar`：

```text
Sidebar: 280–320px
Main Chat: flex
Inspector: 320–380px
```

### 4.2 Page Width

推荐：

- 页面使用 `layout="wide"`
- 内容最大宽度约 1500–1600px
- 不让聊天正文无限拉宽
- Chat 实际阅读宽度建议 720–860px

### 4.3 Vertical Rhythm

基础间距单位：

```text
4px
```

推荐 token：

| Token | Value | Usage |
|---|---:|---|
| `space-1` | 4px | 极小间距 |
| `space-2` | 8px | icon / text |
| `space-3` | 12px | 紧凑控件 |
| `space-4` | 16px | 标准组件 |
| `space-5` | 20px | section 内部 |
| `space-6` | 24px | section 间距 |
| `space-8` | 32px | 大区块 |
| `space-10` | 40px | 页面级间距 |

---

## 5. Color System

设计原则：

- Light-first
- Neutral dominant
- 单一低饱和 Indigo / Blue Accent
- 不使用渐变
- 不使用纯黑大面积背景
- Debug 信息避免彩虹色

### 5.1 Light Theme Tokens

```text
--bg-page:          #F8F9FB
--bg-surface:       #FFFFFF
--bg-subtle:        #F3F4F6
--bg-code:          #F6F7F9

--text-primary:     #17181A
--text-secondary:   #5F6368
--text-muted:       #8B9098

--border-default:   #E4E7EB
--border-strong:    #D5D9DF

--accent:           #4F46E5
--accent-hover:     #4338CA
--accent-soft:      #EEF2FF

--success:          #2F7D4A
--warning:          #9A6700
--danger:           #B42318
```

### 5.2 使用规则

Accent 只用于：

- Primary Button
- Active navigation
- Focus ring
- Source citation active state
- Selected retrieval result

不要用于：

- 每个标题
- 每张卡片
- Debug 数据
- 大面积背景

### 5.3 Status Color

`Indexed`：

- 小圆点 + 文字
- 不使用大号绿色 badge

示例：

```text
● Indexed
```

`Not indexed`：

```text
○ Not indexed
```

---

## 6. Typography

### 6.1 Font Strategy

正文：

```text
Inter / system-ui / -apple-system / Segoe UI / sans-serif
```

代码、Symbol、路径：

```text
JetBrains Mono / SFMono-Regular / Consolas / monospace
```

如果不引入外部字体，优先系统字体。

### 6.2 Type Scale

| Role | Size | Weight |
|---|---:|---:|
| Page title | 22px | 600 |
| Section title | 15px | 600 |
| Body | 14px | 400 |
| Chat answer | 15px | 400 |
| Metadata | 12px | 400 |
| Code | 12.5–13px | 400 |
| Button | 13–14px | 500 |

### 6.3 Rules

- 不使用超大标题
- 标题行高紧凑
- 正文行高 1.55–1.65
- Code 行高 1.5
- 路径和 Symbol 使用 monospace
- 文件名可以半粗体

---

## 7. Radius, Border, Shadow

### Radius

```text
Input:      8px
Button:     8px
Panel:      10px
Code block: 8px
```

### Border

默认：

```text
1px solid #E4E7EB
```

### Shadow

默认不使用。

允许：

- 浮动 Chat Input
- Dropdown
- Popover

阴影必须非常轻：

```text
0 4px 16px rgba(0, 0, 0, 0.06)
```

---

## 8. Header

Header 保持极简。

左：

```text
RepoMind
```

右：

```text
nanoGPT   ● Indexed
```

可选：

```text
Settings
```

不要加入：

- Hero slogan
- 搜索框
- 多级导航
- 大 logo
- GitHub 星标按钮

---

## 9. Repository Panel

### 9.1 Repository Path

Label：

```text
Repository
```

Input：

```text
C:\...\nanoGPT
```

要求：

- 单行
- monospace
- 路径过长允许水平滚动或尾部截断
- 提供 tooltip / caption 展示完整路径

### 9.2 Index Button

Primary action：

```text
Index repository
```

Index 中：

```text
Indexing…
```

完成：

```text
Indexed
```

避免：

```text
🚀 Start AI Knowledge Processing
```

### 9.3 Index Summary

不要用四张 KPI 卡片。

使用紧凑 metadata list：

```text
19 files
90 chunks
AST strategy
Jina Code · 768d
```

可使用：

```text
Files        19
Chunks       90
Chunking     AST
Embedding    Jina Code
```

### 9.4 Advanced Settings

默认折叠：

```text
Advanced
```

可展示：

```text
Chunk size       1200
Chunk overlap     200
Top K               5
RRF K               60
```

第一版 UI 不允许用户随意修改所有 Retrieval 参数。

如果展示，默认只读。

---

## 10. Chat Workspace

### 10.1 Empty State

未开始对话时：

```text
Ask anything about this repository.

Try:
• How is self-attention implemented?
• Where is the training loop?
• How are pretrained weights loaded?
```

不使用插画。

### 10.2 User Message

尽量简单：

```text
You
How is self-attention implemented?
```

可使用非常浅的背景。

不要做大型聊天气泡。

### 10.3 Assistant Message

结构：

```text
RepoMind

Self-attention is implemented in `CausalSelfAttention`...

[Source 1] [Source 2]
```

回答正文保持 720–860px 阅读宽度。

### 10.4 Citations

Citation 样式：

```text
[1] [2]
```

或：

```text
Source 1
```

点击 / 选中 Citation 时：

- 右侧 Inspector 定位对应 Source
- Source item 获得 accent-soft 背景

---

## 11. Chat Input

固定在 Chat Workspace 底部。

Placeholder：

```text
Ask about this repository…
```

要求：

- 不超过两行默认高度
- Enter 发送
- Shift+Enter 换行
- Disable 状态明确
- Repository 未 index 时不可发送

发送按钮：

- 小尺寸
- 仅一个 Primary action
- 不使用大面积 accent

---

## 12. Sources Panel

### 12.1 Source Item

默认结构：

```text
model.py
GPT.from_pretrained

method · lines 206–224
```

顺序：

1. File
2. Qualified Symbol
3. Type + lines
4. 可选简短 preview

### 12.2 Source Card

不要使用厚重 card。

推荐：

```text
────────────────────────
model.py
GPT.from_pretrained
method · 206–224
View source
────────────────────────
```

### 12.3 Source Preview

展开后：

```python
@classmethod
def from_pretrained(...):
    ...
```

要求：

- monospace
- 横向滚动
- 保留缩进
- 不做自动换行或仅允许用户切换
- 最大高度约 320–420px

---

## 13. Retrieval Debug Panel

RepoMind 的关键差异化功能。

默认折叠：

```text
Retrieval details
```

展开后每个结果：

```text
Rank #1

File
model.py

Symbol
CausalSelfAttention.forward

Strategy
ast_symbol

Lines
65–98

Vector rank
1

Vector similarity
0.6554

BM25 rank
3

RRF rank
1
```

### Debug 设计原则

- 使用紧凑 definition list
- 数字右对齐
- 不使用仪表盘
- 不使用 gauge
- 不用彩色进度条
- 不把 similarity 表现成百分比

`0.6554` 就显示：

```text
0.6554
```

不要显示：

```text
65.54% relevant
```

因为 similarity 不是概率。

---

## 14. Insufficient Context State

这是正式产品状态，不是 Error。

标题：

```text
Insufficient repository context
```

正文：

```text
The retrieved repository context does not contain enough
information to answer this question reliably.
```

仍然展示：

```text
Sources
Retrieval details
```

不要隐藏 Retrieval。

不要显示：

```text
Something went wrong
```

---

## 15. Loading States

### Indexing

```text
Indexing repository…
```

阶段：

```text
Reading files
Creating chunks
Generating embeddings
Saving index
```

可以使用简单 progress bar。

不要使用复杂动画。

### Asking

```text
Searching repository…
```

然后：

```text
Generating answer…
```

尽量让 Retrieval 和 Generation 阶段在 UI 上可区分。

---

## 16. Error States

### Invalid Repository Path

```text
Repository path not found.
```

### No Supported Files

```text
No supported .py or .md files were found.
```

### DeepSeek API Error

```text
The language model request failed.
Your repository index is still available.
```

### Embedding Error

```text
The embedding model could not be loaded.
```

Error 文案必须：

- 简洁
- 可操作
- 不暴露 stack trace 给普通用户

Debug 模式下再显示技术错误。

---

## 17. Component Inventory

第一版只需要以下组件：

### Navigation / Layout

- App Header
- Repository Sidebar
- Chat Workspace
- Inspector Panel

### Repository

- Path Input
- Index Button
- Index Status
- Index Metadata
- Advanced Settings Expander

### Chat

- User Message
- Assistant Message
- Citation
- Chat Input
- Empty State
- Loading State
- Refusal State

### Sources

- Source Item
- Source Preview
- Symbol Metadata

### Debug

- Retrieval Result
- Rank Metadata
- Debug Expander

---

## 18. Responsive Behavior

RepoMind 第一版以桌面端优先。

### >= 1200px

三栏：

```text
Repository | Chat | Inspector
```

### 768–1199px

两栏：

```text
Chat | Inspector
```

Repository 移入 sidebar / drawer。

### < 768px

单栏：

```text
Chat
↓
Sources
↓
Retrieval Debug
```

Repository 使用 sidebar。

移动端不是第一阶段重点，但不能完全不可用。

---

## 19. Accessibility

最低要求：

- WCAG AA 对比度
- 所有交互有 keyboard focus
- Focus ring 清晰
- 不只靠颜色表达状态
- Button 有明确文字
- Input 有 label
- Code block 可滚动
- Loading 状态有文字
- Error / refusal 不只使用红色
- 点击区域至少约 36–40px 高

Focus：

```text
2px accent outline
2px offset
```

---

## 20. Motion

默认几乎无动画。

允许：

- 120–180ms hover
- expander 自带动画
- loading spinner
- progress transition

禁止：

- 页面进入动画
- 卡片漂浮
- 无限背景动画
- gradient animation
- parallax

---

## 21. Streamlit Implementation Rules

### 21.1 Page Config

```python
st.set_page_config(
    page_title="RepoMind",
    page_icon="◌",
    layout="wide",
)
```

### 21.2 Model Caching

Embedding Model / Backend 必须缓存。

```python
@st.cache_resource
def load_backend():
    ...
```

不要每次 chat rerun 都重新加载 Jina。

### 21.3 Session State

保存：

```text
messages
repository_path
index_status
current_sources
current_retrieval_results
```

示意：

```python
if "messages" not in st.session_state:
    st.session_state.messages = []
```

### 21.4 Backend Calling

UI 直接调用 Python 函数：

```python
answer, search_results = rag(
    question=prompt,
    top_k=5,
    min_similarity=0,
)
```

不要：

```text
Streamlit
↓
subprocess
↓
python repo_rag.py ask
↓
parse console text
```

---

## 22. File Structure

建议：

```text
repomind/
├── app.py
├── repo_rag.py
├── repo_loader.py
├── chunker.py
├── ast_chunker.py
│
├── ui/
│   ├── __init__.py
│   ├── styles.py
│   └── components.py
│
├── design-system/
│   └── MASTER.md
│
├── evaluation/
│   └── ...
│
└── .gitignore
```

---

## 23. CSS Scope

Streamlit 自定义 CSS 必须克制。

允许修改：

- 页面 padding
- typography
- border
- button radius
- input radius
- code block
- source item
- chat width

不要：

- 大量依赖内部随机 class name
- 用 CSS 强行重构整个 Streamlit DOM
- 使用几十条 brittle selector

自定义 CSS 应集中在：

```text
ui/styles.py
```

---

## 24. Empty / Indexed / Chat / Refusal States

RepoMind 至少必须设计这四个完整状态。

### State A — No Repository

```text
Repository path
[Index repository]

Ask anything about an indexed repository.
```

Chat Input disabled。

### State B — Indexed, No Chat

显示：

```text
nanoGPT · Indexed
19 files · 90 chunks
```

中央显示 suggested questions。

### State C — Active Chat

完整 Answer + Sources + Debug。

### State D — Insufficient Context

回答区域显示 refusal。

右侧 Sources / Debug 仍然存在。

---

## 25. Do / Don't

### Do

- 使用 whitespace 建立层级
- Source 信息优先
- Code 使用 monospace
- Debug 默认折叠
- 状态透明
- 回答引用明确
- 保持界面安静
- 优先桌面开发者体验

### Don't

- 不用 gradient
- 不用 glassmorphism
- 不堆 card
- 不做 dashboard
- 不把 similarity 当概率
- 不给每个 metadata 一个 badge
- 不使用大量 icon
- 不隐藏失败 Retrieval
- 不让聊天气泡占满视觉
- 不加入无关 AI 装饰

---

## 26. v0.1 UI Acceptance Criteria

第一版完成前必须满足：

- [ ] 用户可以输入本地 Repository 路径
- [ ] 用户可以 Index Repository
- [ ] Indexing 有明确 loading 状态
- [ ] Indexed 状态显示 Files / Chunks / Strategy / Embedding
- [ ] 用户可以通过 Chat Input 提问
- [ ] Chat history 在 session 中保留
- [ ] DeepSeek Answer 正常显示
- [ ] Citation 可以对应 Source
- [ ] Source 展示 File / Symbol / Lines
- [ ] Source 可以展开查看代码
- [ ] Retrieval Debug 默认折叠
- [ ] Debug 展示 Vector / BM25 / RRF rank
- [ ] Insufficient Context 有独立正常状态
- [ ] Negative question 不被包装成系统错误
- [ ] Jina Embedding 不会在每次 Streamlit rerun 重新加载
- [ ] `.env` 不暴露
- [ ] 没有 gradient / glassmorphism / KPI card
- [ ] 页面在 1280px+ 桌面宽度下布局稳定

---

## 27. v0.1 Visual Summary

RepoMind 应给人的第一印象：

> 一个安静、精确、面向开发者的代码学习工具。

用户视觉焦点顺序：

```text
Question
↓
Answer
↓
Source
↓
Symbol / Lines
↓
Retrieval Detail
```

而不是：

```text
Logo
↓
Decoration
↓
Cards
↓
Metrics
↓
Answer
```

最终设计原则：

**Answer first. Source always visible. Retrieval explainable. Decoration minimal.**
