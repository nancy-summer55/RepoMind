# nanoGPT Jina Code Embedding Evaluation

## Experiment Goal

Replace the embedding model only (`sentence-transformers/all-MiniLM-L6-v2` -> `jinaai/jina-embeddings-v2-base-code`) and evaluate whether a code-aware embedding improves natural-language-question -> Python-code retrieval. All other variables are unchanged:

`Fixed Chunking -> Vector + BM25 -> RRF -> Dedup -> Top-5 -> DeepSeek`

No reranker, no AST chunking.

---

## Configuration

| Item | Value |
| ---- | ----- |
| target repository | ../target_repos/nanoGPT |
| embedding model | jinaai/jina-embeddings-v2-base-code |
| embedding dimension | 768 |
| chunk strategy | fixed |
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

## Model Download / Loading

- Jina model downloaded and loaded successfully.
- Download size: ~310 MB (`jina-embeddings-v2-base-code` weights) + tiny `jina-bert-v2-qk-post-norm` config module.
- Loading used `SentenceTransformer(..., trust_remote_code=True)`.
- Compatibility note: `jina-embeddings-v2-base-code`'s custom `modeling_bert.py` is incompatible with `transformers>=5` (missing `find_pruneable_heads_and_indices` and `config.is_decoder`). To load it, `transformers` was pinned to `4.51.0` (with `huggingface_hub 0.36.2`, `tokenizers 0.21.4`), plus a small no-op compatibility shim in `repo_rag.py`.

---

## Index Statistics

| Metric | Value |
| ------ | ----- |
| Files indexed | 19 |
| Chunks indexed | 73 |
| Embedding shape | (73, 768) |

Chunk count matched the fixed baseline (73), so evaluation proceeded.

---

## Baseline Metrics

| Metric | all-MiniLM + Hybrid |
| ------ | ------------------: |
| Hit@1 | 66.7% |
| Hit@3 | 83.3% |
| Hit@5 | 100% |

---

## Q1 — Where is the GPT model defined?

Expected: `model.py`

| Rank | File | Lines | Vector Rank | Similarity | BM25 Rank | RRF Rank |
| ---: | ---- | ----- | ----------: | ---------: | --------: | -------: |
| 1 | model.py | 223-243 | 2 | 0.6423 | 2 | 1 |
| 2 | README.md | 1-21 | 1 | 0.6913 | 6 | 2 |
| 3 | sample.py | 40-67 | 5 | 0.6280 | 4 | 3 |
| 4 | README.md | 180-208 | 6 | 0.6235 | 9 | 4 |
| 5 | model.py | 1-34 | 9 | 0.5953 | 8 | 5 |

- Expected Rank: **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q2 — How is self-attention implemented?

Expected: `model.py`

| Rank | File | Lines | Vector Rank | Similarity | BM25 Rank | RRF Rank |
| ---: | ---- | ----- | ----------: | ---------: | --------: | -------: |
| 1 | model.py | 49-66 | 1 | 0.6554 | 1 | 1 |
| 2 | model.py | 1-34 | 2 | 0.6208 | 4 | 2 |
| 3 | model.py | 65-98 | 5 | 0.4964 | 2 | 3 |
| 4 | model.py | 91-128 | 4 | 0.5145 | 5 | 4 |
| 5 | model.py | 164-187 | 3 | 0.5375 | 8 | 5 |

- Expected Rank: **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Q2 Vector improvement:** the correct self-attention chunk (`model.py 49-66`) moved to Vector Rank 1 with similarity 0.6554 (vs 0.1839 and Vector Rank 2 under all-MiniLM).

---

## Q3 — Where is the training loop implemented?

Expected: `train.py`

| Rank | File | Lines | Vector Rank | Similarity | BM25 Rank | RRF Rank |
| ---: | ---- | ----- | ----------: | ---------: | --------: | -------: |
| 1 | train.py | 321-336 | 4 | 0.5301 | 1 | 1 |
| 2 | train.py | 225-257 | 6 | 0.5285 | 6 | 2 |
| 3 | train.py | 1-32 | 3 | 0.5356 | 12 | 3 |
| 4 | README.md | 206-223 | 14 | 0.4800 | 3 | 4 |
| 5 | README.md | 44-73 | 8 | 0.5043 | 10 | 5 |

- Expected Rank: **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q4 — How are configuration values overridden?

Expected: `configurator.py` (primary), `train.py`

| Rank | File | Lines | Vector Rank | Similarity | BM25 Rank | RRF Rank |
| ---: | ---- | ----- | ----------: | ---------: | --------: | -------: |
| 1 | configurator.py | 1-33 | 1 | 0.5686 | 1 | 1 |
| 2 | model.py | 30-51 | 5 | 0.2832 | 9 | 3 |
| 3 | train.py | 76-96 | 3 | 0.4290 | 12 | 4 |
| 4 | train.py | 57-77 | 7 | 0.2514 | 8 | 5 |
| 5 | train.py | 174-198 | 6 | 0.2576 | 10 | 6 |

- Expected Rank: `configurator.py` = **1**, `train.py` = **3**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

Expected: `model.py`

| Rank | File | Lines | Vector Rank | Similarity | BM25 Rank | RRF Rank |
| ---: | ---- | ----- | ----------: | ---------: | --------: | -------: |
| 1 | README.md | 1-21 | 1 | 0.7732 | 1 | 1 |
| 2 | model.py | 205-224 | 5 | 0.6918 | 2 | 2 |
| 3 | sample.py | 40-67 | 3 | 0.7001 | 6 | 3 |
| 4 | train.py | 174-198 | 6 | 0.6856 | 3 | 4 |
| 5 | model.py | 223-243 | 4 | 0.7000 | 12 | 5 |

- Expected Rank: `model.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅

**Q5 README Bias Analysis:** README bias is **not resolved**. `README.md 1-21` remains Rank 1 (vector + BM25 both rank 1). `model.py from_pretrained` stayed at Final Rank 2. Note `from_pretrained`'s Vector Rank actually dropped from 2 (all-MiniLM) to 5 (Jina), even though its similarity rose to 0.6918.

---

## Q6 — How does text generation work?

Expected: `model.py`, `sample.py`

| Rank | File | Lines | Vector Rank | Similarity | BM25 Rank | RRF Rank |
| ---: | ---- | ----- | ----------: | ---------: | --------: | -------: |
| 1 | sample.py | 64-89 | 2 | 0.5099 | 1 | 1 |
| 2 | README.md | 89-108 | 1 | 0.5207 | 8 | 2 |
| 3 | README.md | 18-47 | 12 | 0.4243 | 2 | 3 |
| 4 | sample.py | 1-23 | 7 | 0.4690 | 12 | 4 |
| 5 | data/shakespeare_char/prepare.py | 1-32 | 11 | 0.4356 | 9 | 5 |

- Expected Rank: `sample.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

### Q6 GPT.generate Analysis

| Chunk | all-MiniLM Vector Rank | Jina Vector Rank | Final Rank |
| ----- | ---------------------: | ---------------: | ---------: |
| model.py 292-313 (`generate()`) | 7 | None (not in Top-15) | N/A |
| sample.py 64-89 (generation loop) | 15 | 2 | 1 |

- `sample.py 64-89` improved dramatically (Vector 15 -> 2, Final Rank 1).
- `model.py generate()` did **not** improve; it fell out of the Vector Top-15 entirely (was Rank 7 under all-MiniLM).

---

## Vector Rank Comparison (all-MiniLM vs Jina)

| Question | Key chunk | all-MiniLM Vector Rank | Jina Vector Rank |
| -------- | --------- | ---------------------: | ---------------: |
| Q2 | model.py 49-66 (self-attention) | 2 | 1 (similarity 0.6554) |
| Q5 | model.py 205-224 (from_pretrained) | 2 | 5 |
| Q6 | model.py 292-313 (generate) | 7 | None (not in Top-15) |
| Q6 | sample.py 64-89 (generation loop) | 15 | 2 |

---

## Hit@K

| Metric | all-MiniLM + Hybrid | Jina Code + Hybrid |
| ------ | ------------------: | -----------------: |
| Hit@1 | 66.7% | 83.3% |
| Hit@3 | 83.3% | 100% |
| Hit@5 | 100% | 100% |

- Hit@1: `66.7% -> 83.3%` = **+16.7 pp**
- Hit@3: `83.3% -> 100%` = **+16.7 pp**
- Hit@5: `100% -> 100%` = **0.0 pp**

---

## Retrieval Regressions

- Q5 `from_pretrained` Vector Rank dropped from 2 to 5 (README bias persists).
- Q6 `model.py generate()` fell out of the Vector Top-15 entirely.
- These are localized regressions; overall file-level Hit@K improved.

---

## Conclusion

- Jina Code embedding **improves overall retrieval**: Hit@1 66.7% -> 83.3%, Hit@3 83.3% -> 100%.
- It strongly improves Q2 (self-attention) and Q6 (`sample.py` generation loop).
- It does **not** fix the Q5 README bias, and it does **not** surface `model.py generate()` (that chunk actually dropped out of Vector Top-15).
- **Recommendation:** Yes, `jina-embeddings-v2-base-code` is a better default embedding than `all-MiniLM-L6-v2` for this Python repository retrieval task, with the caveat that Q5/Q6 source-symbol-level recall still needs improvement (e.g., a future reranker or code-aware chunking).
