# RepoMind 新电脑初始化清单

## 1. 解压项目

把压缩包解压到目标目录，例如：

`<project_root>`

建议目录结构最终是：

```text
<project_root>
├── app.py
├── repo_rag.py
├── repo_loader.py
├── ast_chunker.py
├── chunker.py
├── learning\
├── ui\
├── tests\
├── evaluation\
├── docs\
├── README.md
├── requirements.txt
├── .env.example
```

## 2. 进入项目目录

```powershell
Set-Location <project_root>
```

## 3. 准备 Python

确认有可用 Python，例如：

```powershell
<python_executable> --version
```

如果你希望用虚拟环境：

```powershell
<python_executable> -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

如果不使用虚拟环境，后续命令把 `python` 替换成 `<python_executable>`。

## 4. 安装依赖

如果已进入虚拟环境：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果不用虚拟环境：

```powershell
<python_executable> -m pip install --upgrade pip
<python_executable> -m pip install -r requirements.txt
```

## 5. 创建 `.env`

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`。

至少确认这些键存在：

```text
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
EMBEDDING_MODEL=jinaai/jina-embeddings-v2-base-code
EMBEDDING_MODEL_PATH=
```

## 6. 填真实配置

### 必填

把真实的 `DEEPSEEK_API_KEY` 填进去：

```text
DEEPSEEK_API_KEY=你的真实密钥
```

### 二选一处理 embedding 模型

#### 方案 A：新电脑可访问 Hugging Face

保持：

```text
EMBEDDING_MODEL=jinaai/jina-embeddings-v2-base-code
EMBEDDING_MODEL_PATH=
```

首次索引时会懒加载并尝试下载模型。

#### 方案 B：新电脑不能访问 Hugging Face，但你有本地模型目录

设置：

```text
EMBEDDING_MODEL_PATH=<embedding_model_path>
```

这样会优先从本地目录加载。

## 7. 先做基础验证

如果使用虚拟环境：

```powershell
python -m pytest -q
python -m compileall learning app.py ui repo_rag.py
```

如果不用虚拟环境：

```powershell
<python_executable> -m pytest -q
<python_executable> -m compileall learning app.py ui repo_rag.py
```

## 8. 启动应用

虚拟环境下：

```powershell
python -m streamlit run app.py
```

不用虚拟环境：

```powershell
<python_executable> -m streamlit run app.py
```

## 9. 首次运行时预期

你应该能先看到首屏，即使：

- 还没下载 embedding 模型
- 或 API key 配置不完整

当前版本已经做了 preflight 提示，不会在启动阶段直接因为 embedding 或 DeepSeek 阻塞崩掉。

## 10. 做首次功能验证

建议按这个顺序验证：

1. 输入本地仓库路径
2. 点击索引
3. 看是否生成 Learning Map
4. 点击 starter question
5. 提一个 feature 问题
6. 提一个 concept 问题
7. 提一个 negative/refusal 问题
8. 查看 Source Inspector
9. 展开 Retrieval Debug

## 11. 推荐演示问题

可以先用这些问题：

- `Which files should I read first to understand nanoGPT?`
- `How is self-attention implemented?`
- `What does attention mask do in this codebase?`
- `How does nanoGPT perform reinforcement learning from human feedback?`

## 12. 常见问题排查

### 1. app 能启动，但索引时报 embedding 错误

说明：

- `EMBEDDING_MODEL_PATH` 配错
- 或 Hugging Face 不可达且本地无缓存

处理：

- 检查 `.env` 中的 `EMBEDDING_MODEL_PATH`
- 或提供本地模型目录
- 或确保能访问 Hugging Face

### 2. 问答时报 DeepSeek 错误

说明：

- `DEEPSEEK_API_KEY` 缺失、占位、无效或网络不可达

处理：

- 检查 `.env` 中的 `DEEPSEEK_API_KEY`

### 3. 测试通过，但 live flow 跑不通

说明：

- 自动化测试主要覆盖模块逻辑
- live flow 仍依赖真实模型与网络条件

处理：

- 先检查 `.env`
- 再检查 embedding 模型来源
- 再检查本地测试仓库路径是否存在

## 13. 当前版本限制

当前明确限制：

- 仅支持 Python / Markdown
- 无 multi-language AST
- 无完整 call graph
- 无代码编辑
- 无 MCP
- 无 local LLM
- single-repo focus
- symbol-level retrieval 仍可能弱于 file-level retrieval

## 14. 建议继续开发前先确认

继续开发前，建议先确认：

- `pytest` 全绿
- `streamlit run app.py` 能启动
- 本地能完成至少一次真实索引
- Learning Map 和 Guided Q&A 至少各跑通一轮
