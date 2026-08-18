# RepoMind Release Checklist

本清单用于发布或对外分享当前 Learning MVP 前的人工检查。只覆盖当前已经实现或已经具备的能力，不把未来功能列为发布前要求。

## 1. Functional Checklist

- [ ] 可以启动 Streamlit 应用。
- [ ] 可以输入本地仓库路径。
- [ ] 本地 Python / Markdown 仓库可以索引成功。
- [ ] 索引成功后显示仓库名称、文件数、chunk 数、chunking 策略和 embedding 信息。
- [ ] 索引成功后自动生成 Learning Map。
- [ ] Learning Map 生成失败时，仓库索引仍然可用，chat 仍然可用。
- [ ] Learning Map 中的 starter questions 可以点击。
- [ ] 点击 starter question 后会进入同一个 `ask()` 问答流程。
- [ ] 手动输入 feature 问题可以走通。
- [ ] 手动输入 concept 问题可以走通。
- [ ] 手动输入 configuration 问题可以走通。
- [ ] 手动输入 negative/refusal 问题可以走通。
- [ ] Guided Q&A 回答能保存 `content`、`sources`、`followups`、`intent`、`refusal`。
- [ ] Assistant answer 下方显示 3 个 follow-up questions。
- [ ] 点击 follow-up question 后会进入同一个 `ask()` 问答流程。
- [ ] Evidence 不足时可以显示 refusal 或 insufficient context。

## 2. UX Checklist

- [ ] Repository 面板可以输入路径并触发索引。
- [ ] 索引中和索引完成状态对用户可理解。
- [ ] Learning Map 出现在 chat 区域顶部。
- [ ] Learning Map starter questions 可点击。
- [ ] Chat 中用户消息和 assistant answer 能正常显示。
- [ ] Assistant structured answer 按 Markdown 显示。
- [ ] Follow-up buttons 显示在对应 assistant answer 下方。
- [ ] Source buttons 不被 follow-up buttons 破坏。
- [ ] 点击 Source button 后右侧 Source Inspector 更新。
- [ ] Source Inspector 可以显示文件、符号、行号和源码片段。
- [ ] Source Inspector 可以显示 `source_role`。
- [ ] Source Inspector 可以显示 `relevance_reason`。
- [ ] Retrieval Debug 可以展开查看。
- [ ] Retrieval Debug 显示 vector / BM25 / RRF rank 和 score。
- [ ] Refusal 或错误提示不会让用户误以为索引丢失。

## 3. Documentation Checklist

- [ ] `README.md` 已定位为 AI 开源项目学习助手。
- [ ] `README.md` 明确说明 Learning Map、Guided Q&A、Source Evidence。
- [ ] `README.md` 明确当前已实现能力。
- [ ] `README.md` 明确当前技术栈：Streamlit、Chroma、Jina embeddings、BM25、RRF、DeepSeek。
- [ ] `README.md` 明确当前限制。
- [ ] `RepoMind_User_Guide.md` 已存在。
- [ ] `RepoMind_User_Guide.md` 说明如何索引本地仓库。
- [ ] `RepoMind_User_Guide.md` 说明如何阅读 Learning Map。
- [ ] `RepoMind_User_Guide.md` 说明如何使用 starter questions 和 follow-ups。
- [ ] `RepoMind_User_Guide.md` 说明如何查看 Source Inspector 和 Retrieval Debug。
- [ ] `RepoMind_Dev_Setup.md` 已存在。
- [ ] `RepoMind_Dev_Setup.md` 说明 Python 版本、依赖安装、`.env` 和启动方式。
- [ ] `RepoMind_Demo_Script.md` 已存在。
- [ ] `RepoMind_Demo_Script.md` 和 README / User Guide 描述一致。
- [ ] 文档没有把未实现功能写成已支持。

## 4. Evaluation Checklist

- [ ] `evaluation/learning_eval_questions.json` 已存在。
- [ ] `evaluation/learning_eval_questions.json` 是合法 JSON。
- [ ] Learning eval dataset 当前覆盖 nanoGPT。
- [ ] Learning eval dataset 至少包含 overview 问题。
- [ ] Learning eval dataset 至少包含 feature 问题。
- [ ] Learning eval dataset 至少包含 concept 问题。
- [ ] Learning eval dataset 至少包含 configuration 问题。
- [ ] Learning eval dataset 至少包含 negative/refusal 问题。
- [ ] 每条 eval question 包含 `id`、`repository`、`question`、`type`、`expected_files`、`expected_symbols`、`negative`、`notes`。
- [ ] `evaluation/learning_eval_template.md` 已存在。
- [ ] 人工评测模板包含 Retrieval Result 检查。
- [ ] 人工评测模板包含 Answer Grounding 检查。
- [ ] 人工评测模板包含 Learning Usefulness 检查。
- [ ] 人工评测模板包含 Follow-Up Quality 检查。
- [ ] 人工评测模板包含 Refusal Check。
- [ ] 人工评测模板包含 Failure Classification。
- [ ] 人工评测模板包含 Final Judgment。

## 5. Demo Checklist

- [ ] 本地已准备 nanoGPT 仓库。
- [ ] Demo 前确认 `.env` 中有有效 `DEEPSEEK_API_KEY`。
- [ ] Demo 前确认依赖已安装。
- [ ] Demo 前确认可以启动 `streamlit run app.py`。
- [ ] Demo 中可以输入 nanoGPT 本地路径。
- [ ] Demo 中可以完成索引。
- [ ] Demo 中可以展示 Learning Map。
- [ ] Demo 中可以点击 starter question。
- [ ] Demo 中可以提 feature 问题：`How is self-attention implemented?`
- [ ] Demo 中可以提 concept 问题：`What does attention mask do in this codebase?`
- [ ] Demo 中可以提 negative/refusal 问题：`How does nanoGPT perform reinforcement learning from human feedback?`
- [ ] Demo 中可以点击 Sources。
- [ ] Demo 中可以展开 Retrieval Debug。
- [ ] Demo 中主动说明当前限制，不超卖未实现能力。

## 6. Environment / Config Checklist

- [ ] `requirements.txt` 已存在。
- [ ] `requirements.txt` 包含 Streamlit。
- [ ] `requirements.txt` 包含 Chroma。
- [ ] `requirements.txt` 包含 sentence-transformers。
- [ ] `requirements.txt` 包含 BM25 相关依赖。
- [ ] `requirements.txt` 包含 OpenAI-compatible client 依赖。
- [ ] `.env.example` 已存在。
- [ ] `.env.example` 包含 `DEEPSEEK_API_KEY`。
- [ ] `.env.example` 包含 `DEEPSEEK_MODEL`。
- [ ] `.env.example` 包含 `EMBEDDING_MODEL`。
- [ ] 文档说明 `.env` 需要手动从 `.env.example` 复制。
- [ ] 文档说明真实 API key 不应提交。
- [ ] 文档说明启动命令为 `streamlit run app.py`。
- [ ] 文档说明 Windows 下可使用本地绝对路径作为 repo path。
- [ ] 文档说明 DeepSeek 调用依赖网络和 API 可用性。
- [ ] 文档说明首次加载 embedding model 可能较慢。

## 7. Known Limitations Checklist

- [ ] 文档明确当前只支持 Python / Markdown。
- [ ] 文档明确只有 Python 支持 AST-aware chunking。
- [ ] 文档明确不支持 multi-language AST。
- [ ] 文档明确不支持完整 call graph。
- [ ] 文档明确不支持代码编辑。
- [ ] 文档明确不支持 MCP。
- [ ] 文档明确不支持 local LLM。
- [ ] 文档明确当前以 single-repo learning 为主。
- [ ] 文档明确重新索引会重建当前 Chroma collection。
- [ ] 文档明确 BM25 当前按查询构建。
- [ ] 文档明确 DeepSeek 依赖网络和 API。
- [ ] 文档明确 symbol-level retrieval 仍可能弱于 file-level retrieval。
- [ ] 文档明确 Learning Map 是 grounded learning aid，不是完整架构证明。

## 8. Pre-Share Final Review

- [ ] `git diff --check` 通过。
- [ ] `git status --short` 已检查。
- [ ] 没有意外修改 `repo_rag.py`。
- [ ] 没有意外修改 `learning/` 功能模块。
- [ ] 没有意外修改 `ui/styles.py`。
- [ ] 如果本次发布包含 `app.py` / `ui/components.py` 改动，确认它们属于 Guided Q&A 接入范围。
- [ ] README、User Guide、Developer Setup、Demo Script、Release Checklist 之间说法一致。
- [ ] 评测资产和人工评测模板已纳入分享材料。
- [ ] Demo 问题来自当前 nanoGPT learning eval dataset 或与其一致。
- [ ] 已主动准备 Known Limitations 说明。
- [ ] 没有把未来功能写成当前已支持。
