# nanoGPT Jina + AST Evaluation

## Experiment Goal

Keep the best stable embedding (Jina Code) and change ONLY `chunk_strategy: fixed -> ast`, to test whether Jina can unlock the value of AST-aware symbol chunks, especially for `GPT.generate` and `GPT.from_pretrained`.

Pipeline:

`AST/Fixed Chunking -> Vector + BM25 -> RRF -> Dedup -> Top-5 -> DeepSeek`

No reranker is used.

---

## Configuration

| Item | Value |
| ---- | ----- |
| target repository | ../target_repos/nanoGPT |
| embedding model | jinaai/jina-embeddings-v2-base-code |
| embedding dimension | 768 |
| chunk strategy | ast |
| chunk_size | 1200 |
| chunk_overlap | 200 |
| Vector candidate_k | 15 |
| BM25 candidate_k | 15 |
| RRF_K | 60 |
| dedup overlap threshold | 0.30 |
| final top_k | 5 |
| similarity threshold | 0 (gate disabled) |
| reranker | disabled |

---

## Jina Fixed Baseline

| Metric | Value |
| ------ | ----- |
| File Hit@1 | 83.3% |
| File Hit@3 | 100% |
| File Hit@5 | 100% |

---

## AST Chunk Statistics

| Metric | Value |
| ------ | ----- |
| Python files | 15 |
| Other files | 4 |
| AST symbol chunks | 28 (17 ast_symbol + 11 ast_symbol_split) |
| AST residual chunks | 39 |
| Class context chunks | 6 |
| Fixed / Markdown chunks | 17 |
| Total chunks | 90 |
| Files indexed | 19 |
| Embedding shape | (90, 768) |

---

## AST Symbol Sanity Check

| Symbol | Result |
| ------ | ------ |
| CausalSelfAttention.__init__ | ✅ found |
| CausalSelfAttention.forward | ✅ found |
| GPT.from_pretrained | ✅ found (3 split chunks) |
| GPT.generate | ✅ found (2 split chunks) |
| train.py ast_residual | ✅ 14 chunks |

---

## Q1 — Where is the GPT model defined?

Expected: `model.py`

Final Top-5: `model.py` Rank 1 (model.py 223-243, 1-17, 118-119 `GPT` class context, 206-224).

- Expected Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q2 — How is self-attention implemented?

Expected: `model.py`, symbol `CausalSelfAttention.*`

| Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | model.py | 52-70 | ast_symbol_split | CausalSelfAttention.forward |
| 2 | model.py | 31-50 | ast_symbol | CausalSelfAttention.__init__ |
| 3 | model.py | 29-30 | ast_class_context | CausalSelfAttention |
| 4 | model.py | 103-106 | ast_symbol | Block.forward |
| 5 | model.py | 170-193 | ast_symbol | GPT.forward |

- Expected File Rank: **1** · Expected Symbol Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Symbol Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

Dedup removed `model.py 68-76` (overlap ratio 0.33).

---

## Q3 — Where is the training loop implemented?

Expected: `train.py`, `ast_residual`

Final Top-5: all `train.py` `ast_residual` chunks; `train.py 243-274` Rank 1 (contains `# training loop` + `while True:`).

- Expected File Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q4 — How are configuration values overridden?

Expected: `configurator.py` (primary), `train.py`

| Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | configurator.py | 1-33 | ast_residual | |
| 2 | model.py | 279-287 | ast_symbol_split | GPT.configure_optimizers |
| 3 | train.py | 76-96 | ast_residual | |
| 4 | model.py | 263-279 | ast_symbol_split | GPT.configure_optimizers |
| 5 | model.py | 52-70 | ast_symbol_split | CausalSelfAttention.forward |

- Expected File Rank: `configurator.py` = **1**, `train.py` = **3**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

Expected: `model.py`, symbol `GPT.from_pretrained`

| Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | model.py | 206-224 | ast_symbol_split | GPT.from_pretrained |
| 2 | README.md | 1-21 | fixed_markdown | |
| 3 | model.py | 242-261 | ast_symbol_split | GPT.from_pretrained |
| 4 | model.py | 223-243 | ast_symbol_split | GPT.from_pretrained |
| 5 | train.py | 176-199 | ast_residual | |

- Expected File Rank: **1** · Expected Symbol Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Symbol Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Q5 Analysis:** `GPT.from_pretrained` improved from Vector Rank 5 (Jina+Fixed) to Vector Rank 1, and Final Rank 2 -> 1. README bias is resolved for Q5.

---

## Q6 — How does text generation work?

Expected: `model.py` / `sample.py`, symbol `GPT.generate`

| Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | sample.py | 64-89 | ast_residual | |
| 2 | README.md | 18-47 | fixed_markdown | |
| 3 | README.md | 106-122 | fixed_markdown | |
| 4 | README.md | 89-108 | fixed_markdown | |
| 5 | data/openwebtext/readme.md | 1-15 | fixed_markdown | |

- Expected File Rank: `sample.py` = **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

### Q6 GPT.generate Analysis

| Chunk | Vector Rank | BM25 Rank | RRF Rank | Final Rank |
| ----- | ----------: | --------: | -------: | ---------: |
| model.py 305-323 (`GPT.generate` part 1) | None | 4 | 10 | N/A |
| model.py 322-330 (`GPT.generate` part 2) | None | 3 | 8 | N/A |
| sample.py 64-89 (generation loop) | 8 | 1 | 1 | 1 |

- **Verdict:** `AST + Jina did not solve GPT.generate retrieval` — the two `GPT.generate` split chunks are BM25-strong but Vector-weak (not in Vector Top-15), so RRF ranks them 8/10, outside the final Top-5. `sample.py` generation loop is retained at Final Rank 1.

---

## File Hit@K

| Metric | Value |
| ------ | ----- |
| File Hit@1 | 6 / 6 = 100% |
| File Hit@3 | 6 / 6 = 100% |
| File Hit@5 | 6 / 6 = 100% |

---

## Symbol Hit@K

| Question | Expected symbol | Final Rank | Hit@1 | Hit@3 | Hit@5 |
| -------- | --------------- | ---------: | ----- | ----- | ----- |
| Q2 | CausalSelfAttention.* | 1 | ✅ | ✅ | ✅ |
| Q5 | GPT.from_pretrained | 1 | ✅ | ✅ | ✅ |
| Q6 | GPT.generate | N/A | ❌ | ❌ | ❌ |

| Metric | Value |
| ------ | ----- |
| Symbol Hit@1 | 2 / 3 = 66.7% |
| Symbol Hit@3 | 2 / 3 = 66.7% |
| Symbol Hit@5 | 2 / 3 = 66.7% |

---

## Jina Fixed vs Jina AST

| Metric | Jina + Fixed | Jina + AST | Change |
| ------ | -----------: | ---------: | -----: |
| File Hit@1 | 83.3% | 100% | +16.7 pp |
| File Hit@3 | 100% | 100% | 0.0 pp |
| File Hit@5 | 100% | 100% | 0.0 pp |

---

## Regression Check

- Q3: `train.py ast_residual` still Top-1 ✅
- Q4: `configurator.py` still Rank 1 ✅
- Q6: `sample.py` generation loop retained at Final Rank 1 ✅
- No file-level Hit@K regression.

---

## Conclusion

- **Jina + AST achieves perfect file-level retrieval** on this 6-question set: File Hit@1/3/5 = 100% / 100% / 100% (up from 83.3% / 100% / 100% in Jina+Fixed).
- AST symbol chunks + Jina clearly help Q2 and Q5: `CausalSelfAttention.*` and `GPT.from_pretrained` now both rank Top-1, and Q5's README bias is resolved.
- **Q6 `GPT.generate` remains unsolved** — it is split into two chunks, is BM25-strong but Vector-weak, and still misses the final Top-5.
- **Recommendation:** Yes, adopt `Jina + AST` as the new default. It is strictly better than `Jina + Fixed` on file Hit@1 and resolves Q5; the remaining Q6 `GPT.generate` issue points to a future reranker/code-embedding improvement rather than chunking alone.
