# nanoGPT AST-aware Chunking Evaluation

## Experiment Goal

Change ONLY Python chunking from fixed-size chunking to AST-aware chunking, and evaluate whether source-structure-aware chunks improve code retrieval, under the unchanged Hybrid retrieval pipeline:

`Question -> Vector Top-15 + BM25 Top-15 -> RRF -> Dedup -> Top-5 -> DeepSeek`

No reranker is used. Embedding model, BM25 tokenizer/params, RRF_K, dedup threshold, and top_k are unchanged.

---

## Configuration

| Item | Value |
| ---- | ----- |
| target repository | ../target_repos/nanoGPT |
| embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| embedding dimension | 384 |
| chunk_size | 1200 |
| chunk_overlap | 200 |
| chunk strategy | ast |
| Vector candidate_k | 15 |
| BM25 candidate_k | 15 |
| RRF_K | 60 |
| dedup overlap threshold | 0.30 |
| final top_k | 5 |
| similarity threshold | 0 (gate disabled) |
| reranker | disabled |

---

## Fixed Chunking Statistics

| Metric | Value |
| ------ | ----- |
| Total chunks | 73 |

---

## AST Chunking Statistics

| Metric | Value |
| ------ | ----- |
| Files loaded | 19 |
| Python files | 15 |
| Other files | 4 |
| AST symbol chunks | 28 (17 ast_symbol + 11 ast_symbol_split) |
| AST residual chunks | 39 |
| Class context chunks | 6 |
| Fixed / Markdown chunks | 17 |
| Total chunks | 90 |
| Embedding shape | (90, 384) |

---

## AST Symbol Sanity Check

| Symbol | Result |
| ------ | ------ |
| CausalSelfAttention.__init__ | ✅ found |
| CausalSelfAttention.forward | ✅ found |
| GPT.from_pretrained | ✅ found (model.py 206-224, ast_symbol_split) |
| GPT.generate | ✅ found (model.py 305-323 / 322-330, ast_symbol_split) |
| train.py ast_residual chunks | ✅ 14 chunks |

---

## Q1 — Where is the GPT model defined?

Expected file: `model.py`

| Final Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | model.py | 1-17 | ast_residual | |
| 2 | model.py | 118-119 | ast_class_context | GPT |
| 3 | model.py | 206-224 | ast_symbol_split | GPT.from_pretrained |
| 4 | model.py | 223-243 | ast_symbol_split | GPT.from_pretrained |
| 5 | sample.py | 40-67 | ast_residual | |

- Expected File Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q2 — How is self-attention implemented?

Expected file: `model.py` · Expected symbol: `CausalSelfAttention.*`

| Final Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | model.py | 52-70 | ast_symbol_split | CausalSelfAttention.forward |
| 2 | model.py | 29-30 | ast_class_context | CausalSelfAttention |
| 3 | model.py | 87-92 | ast_symbol | MLP.forward |
| 4 | model.py | 26-27 | ast_symbol | LayerNorm.forward |
| 5 | model.py | 103-106 | ast_symbol | Block.forward |

- Expected File Rank: **1** · Expected Symbol Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Symbol Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Q2 Self-Attention Analysis:** AST produced a dedicated `CausalSelfAttention.forward` chunk that ranked Top-1 with vector similarity 0.4012 (vs 0.2789 in fixed chunking). This is the clearest AST improvement.

---

## Q3 — Where is the training loop implemented?

Expected file: `train.py` · Expected chunk type: `ast_residual`

| Final Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | train.py | 243-274 | ast_residual | |
| 2 | README.md | 206-223 | fixed_markdown | |
| 3 | README.md | 1-21 | fixed_markdown | |
| 4 | train.py | 57-77 | ast_residual | |
| 5 | train.py | 293-313 | ast_residual | |

- Expected File Rank: **1**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Q3 Residual Code Analysis:** `train.py 243-274` (contains `# training loop` + `while True:`) is an `ast_residual` chunk and ranks Top-1. AST did NOT drop module-level training loop code.

---

## Q4 — How are configuration values overridden?

Expected files: `configurator.py` (primary), `train.py`

| Final Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | configurator.py | 1-33 | ast_residual | |
| 2 | model.py | 206-224 | ast_symbol_split | GPT.from_pretrained |
| 3 | train.py | 76-96 | ast_residual | |
| 4 | model.py | 31-50 | ast_symbol | CausalSelfAttention.__init__ |
| 5 | README.md | 44-73 | fixed_markdown | |

- Expected File Rank: `configurator.py` = **1**, `train.py` = **3**
- File Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Note:** `configurator.py` kept Rank 1; no MS MARCO-style regression here.

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

Expected file: `model.py` · Expected symbol: `GPT.from_pretrained`

| Final Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | README.md | 1-21 | fixed_markdown | |
| 2 | model.py | 206-224 | ast_symbol_split | GPT.from_pretrained |
| 3 | train.py | 176-199 | ast_residual | |
| 4 | model.py | 162-168 | ast_symbol | GPT._init_weights |
| 5 | README.md | 157-165 | fixed_markdown | |

- Expected File Rank: **2** · Expected Symbol Rank: **2**
- File Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Symbol Hit@1: ❌  Hit@3: ✅  Hit@5: ✅

**Q5 from_pretrained Analysis:** `GPT.from_pretrained` is now a clean dedicated symbol chunk (model.py 206-224) at Rank 2, but `README.md 1-21` still holds Rank 1. README bias was not resolved.

---

## Q6 — How does text generation work?

Expected files: `model.py`, `sample.py` · Expected symbol: `GPT.generate`

| Final Rank | File | Lines | Strategy | Symbol |
| ---: | ---- | ----- | -------- | ------ |
| 1 | README.md | 18-47 | fixed_markdown | |
| 2 | data/shakespeare_char/prepare.py | 1-31 | ast_residual | |
| 3 | README.md | 157-165 | fixed_markdown | |
| 4 | data/openwebtext/readme.md | 1-15 | fixed_markdown | |
| 5 | data/openwebtext/prepare.py | 27-60 | ast_residual | |

- Expected File Rank: **N/A** · Expected Symbol Rank: **N/A**
- File Hit@1: ❌  Hit@3: ❌  Hit@5: ❌
- Symbol Hit@1: ❌  Hit@3: ❌  Hit@5: ❌

### Q6 GPT.generate Analysis

| Chunk | Vector Rank | BM25 Rank | RRF Rank | Final Rank |
| ----- | ----------: | --------: | -------: | ---------: |
| model.py 305-323 (`GPT.generate` part 1) | None | 4 | 12 | N/A |
| model.py 322-330 (`GPT.generate` part 2) | None | 3 | 11 | N/A |
| sample.py 64-89 (generation loop) | None | 1 | 9 | N/A |
| sample.py 1-23 | 14 | 15 | 7 | N/A |

**Verdict:** AST did **not** surface `GPT.generate` into the final Top-5. The two `GPT.generate` split chunks are BM25-strong (rank 3/4) but Vector-weak (not in Vector Top-15), so RRF ranks them 11/12. `sample.py 64-89` dropped out of the Vector Top-15 entirely under the AST index (its enriched index_text changed vector ranking), so its RRF rank fell from 4 (fixed) to 9 and it missed the final Top-5.

---

## File Hit@K

| Metric | Value |
| ------ | ----- |
| File Hit@1 | 4 / 6 = 66.7% |
| File Hit@3 | 5 / 6 = 83.3% |
| File Hit@5 | 5 / 6 = 83.3% |

---

## Symbol Hit@K

| Question | Expected symbol | Final rank | Hit@1 | Hit@3 | Hit@5 |
| -------- | --------------- | ---------: | ----- | ----- | ----- |
| Q2 | CausalSelfAttention.* | 1 | ✅ | ✅ | ✅ |
| Q5 | GPT.from_pretrained | 2 | ❌ | ✅ | ✅ |
| Q6 | GPT.generate | N/A | ❌ | ❌ | ❌ |

| Metric | Value |
| ------ | ----- |
| Symbol Hit@1 | 1 / 3 = 33.3% |
| Symbol Hit@3 | 2 / 3 = 66.7% |
| Symbol Hit@5 | 2 / 3 = 66.7% |

---

## Fixed Hybrid vs AST Hybrid

| Metric | Fixed Hybrid | AST Hybrid | Change |
| ------ | -----------: | ---------: | -----: |
| File Hit@1 | 66.7% | 66.7% | 0.0 pp |
| File Hit@3 | 83.3% | 83.3% | 0.0 pp |
| File Hit@5 | 100% | 83.3% | -16.7 pp |

---

## Retrieval Problems

- Q6 file-level retrieval regressed: `sample.py` and `model.py` both missed the final Top-5 (Hit@5 100% -> 83.3%).
- `GPT.generate` split chunks are BM25-only; the Vector retriever did not rank them in its Top-15, so RRF could not promote them.
- `sample.py 64-89` lost its Vector Top-15 membership under the AST index (vector rank went from 15 in fixed to None), which dropped its RRF rank from 4 to 9.
- Q5 README bias persists (`README.md 1-21` still Rank 1).
- The all-MiniLM-L6-v2 embedding does not appear to exploit the `File/Symbol/Type` header added to `index_text` for behavioral questions.

---

## Conclusion

- **AST integration is successful and symbol chunks are well-formed** (Q2 improved, Q3/Q4 did not regress, Q5/Q6 symbols exist as dedicated chunks).
- **File Hit@K is unchanged at Hit@1/Hit@3 (66.7% / 83.3%) but Hit@5 regressed from 100% to 83.3%** because Q6 lost both target files.
- **Symbol retrieval is partial:** `CausalSelfAttention.forward` and `GPT.from_pretrained` are retrieved, but `GPT.generate` is still not surfaced.
- **Recommendation:** Do NOT make AST-aware chunking the new default yet. It improves code-structure granularity (Q2) but the current embedding model does not turn symbol headers into better recall for Q6. Before adopting AST as default, pair it with a code-aware embedding or investigate why `sample.py`/`GPT.generate` fall out of the Vector Top-15.
