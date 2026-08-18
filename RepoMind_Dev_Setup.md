# RepoMind Developer Setup Guide

## 1. 开发环境前提

RepoMind 当前是一个本地 Streamlit 应用，用来索引本地 Python / Markdown 仓库，并通过 DeepSeek 生成 Learning Map 和 Guided Q&A 回答。

开发前需要准备：

- Windows、macOS 或 Linux 终端环境。
- 可用 Python 环境。当前开发环境使用过 Python 3.13。
- 可以访问本地文件系统中的 RepoMind 项目目录。
- 一个可用于测试的本地代码仓库，例如 nanoGPT。
- 可用的 DeepSeek API key。
- 首次运行时需要能安装 Python 依赖，并可能需要下载 embedding 模型。

当前项目没有提供一键安装脚本。环境准备需要手动完成。

## 2. Python 版本与依赖安装

README 记录的开发环境是 Python 3.13 on Windows CPU。建议优先使用 Python 3.13 或与依赖兼容的 Python 版本。

在仓库根目录创建虚拟环境：

```bash
python -m venv .venv
```

Windows 激活虚拟环境：

```bash
.venv\Scripts\activate
```

macOS / Linux 激活虚拟环境：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

当前 `requirements.txt` 中的主要依赖包括：

- `streamlit`
- `chromadb`
- `sentence-transformers`
- `rank-bm25`
- `nltk`
- `openai`
- `python-dotenv`
- `numpy`
- `torch`
- `transformers`
- `huggingface_hub`
- `tokenizers`
- `accelerate`

注意：`jinaai/jina-embeddings-v2-base-code` 依赖 `transformers < 5`。仓库已在 `requirements.txt` 中固定相关版本，并且 `repo_rag.py` 中有兼容 shim。

## 3. `.env` 配置说明

仓库提供 `.env.example`，需要手动复制为 `.env`：

```bash
cp .env.example .env
```

Windows PowerShell 也可以手动复制该文件，或使用：

```powershell
Copy-Item .env.example .env
```

`.env` 至少需要配置：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
EMBEDDING_MODEL=jinaai/jina-embeddings-v2-base-code
```

字段说明：

- `DEEPSEEK_API_KEY`：必填。用于 DeepSeek 生成 Learning Map 和回答。
- `DEEPSEEK_MODEL`：可保留默认值 `deepseek-chat`。
- `EMBEDDING_MODEL`：可保留默认值 `jinaai/jina-embeddings-v2-base-code`。

`.env` 已被 git 忽略，不应提交真实 API key。

## 4. 如何启动 Streamlit

在 RepoMind 根目录启动：

```bash
streamlit run app.py
```

启动后在浏览器中打开 Streamlit 给出的本地地址。

基本验证流程：

1. 在左侧 Repository 面板输入一个本地仓库路径。
2. 点击 **Index repository**。
3. 等待索引完成。
4. 查看 Learning Map 是否出现。
5. 点击 starter question 或手动输入问题。
6. 查看回答、Sources 和 Retrieval details。

## 5. Windows 环境注意事项

Windows 下建议注意：

- 路径可以使用类似 `D:\path\to\repo` 的本地目录。
- 如果 PowerShell 中 `python` 不可用，可以使用实际 Python 路径或 `py` launcher。
- 当前机器曾使用 `<python_executable>` 运行测试和编译检查。
- 首次加载 Jina embedding 模型可能较慢。
- 如果 Hugging Face cache 已经存在，`app.py` 会设置离线环境变量，减少重复网络检查。
- DeepSeek 调用需要网络和有效 API key。
- PowerShell 中某些重定向到 `NUL` 的命令可能和 `cmd` 行为不同；文档验证时可使用 `cmd /c`。

## 6. 如何准备一个本地仓库做测试

RepoMind 索引的是本地目录，不会自动下载演示仓库。

手动准备一个测试仓库，例如 nanoGPT：

1. 在本机准备 nanoGPT 的本地 clone。
2. 确认该目录中有 `.py` 或 `.md` 文件。
3. 在 RepoMind UI 左侧输入该本地路径。
4. 点击 **Index repository**。

当前 loader 只会读取 `.py` 和 `.md` 文件，并会跳过常见依赖目录、生成目录和过大的文件。

## 7. 当前已知限制

当前实现限制：

- 只支持 Python / Markdown 文件。
- 只有 Python 支持 AST-aware chunking。
- 不支持 multi-language AST。
- 不支持完整 call graph。
- 不支持代码编辑。
- 不支持 MCP。
- 不支持 local LLM。
- 当前主要面向单仓库学习。
- 重新索引会重建当前 Chroma collection。
- BM25 当前按查询从 Chroma collection 构建。
- DeepSeek 生成依赖网络和 API 可用性。
- Symbol-level retrieval 仍可能弱于 file-level retrieval。
- Learning Map 是 grounded learning aid，不是完整架构证明。

## 8. 常见启动问题排查

### 找不到 Python

先确认 Python 是否可执行：

```powershell
where.exe python
where.exe py
py -0p
```

如果项目内已有虚拟环境，优先激活虚拟环境。否则手动安装兼容 Python 版本后再创建 `.venv`。

### 依赖安装失败

先确认当前正在使用预期 Python：

```bash
python --version
python -c "import sys; print(sys.executable)"
```

然后重新执行：

```bash
pip install -r requirements.txt
```

如果失败来自模型或 PyTorch 相关依赖，需要按当前机器和 Python 版本处理，但不要随意升级 `transformers` 到 5.x，因为 Jina embedding 兼容性依赖当前 pin。

### 缺少 DeepSeek API key

如果看到 `DEEPSEEK_API_KEY was not found`，检查：

- 是否已从 `.env.example` 复制出 `.env`。
- `.env` 是否位于 RepoMind 根目录。
- `DEEPSEEK_API_KEY` 是否已填真实值。

### 索引时没有文件

如果提示没有支持文件，检查被索引目录是否包含 `.py` 或 `.md` 文件。

RepoMind 当前不会索引其他语言文件，也不会索引被 loader 忽略的目录。

### Learning Map 生成失败

Learning Map 生成失败不代表索引失败。当前设计是 fail open：

- 仓库索引仍然可用。
- Chat 仍可继续使用。
- UI 会显示 Learning Map 生成失败信息。

常见原因包括 DeepSeek API key、网络、模型响应为空或超时。

### 回答显示 insufficient context

这通常表示 retrieved sources 不足以支持问题，或问题问到了仓库没有实现的能力。

建议：

- 查看 Sources 是否相关。
- 展开 Retrieval details 检查命中文件和排名。
- 把问题改得更贴近仓库文件、符号或功能。

### 首次启动或首次索引很慢

可能原因：

- 首次安装或加载 embedding 模型。
- 首次构建 Chroma index。
- 本地仓库文件较多。
- DeepSeek 网络调用延迟。

这是当前实现的正常边界，仓库还没有增量索引或本地 LLM 模式。
