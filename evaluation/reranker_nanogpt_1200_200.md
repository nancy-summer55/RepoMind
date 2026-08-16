# nanoGPT Hybrid + CrossEncoder Reranker Evaluation

## Experiment Goal

Evaluate `Vector + BM25 + RRF + CrossEncoder Reranker + Dedup` and compare with the Hybrid (no reranker) version.

No code, parameters, embedding, chunking, BM25, RRF, dedup, reranker, or DeepSeek configuration was changed during this evaluation. No re-index was performed (existing 73-chunk nanoGPT 1200/200 index reused).

---

## Configuration

| Item | Value |
| ---- | ----- |
| target repository | ../target_repos/nanoGPT |
| embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| embedding dimension | 384 |
| chunk_size | 1200 |
| chunk_overlap | 200 |
| Vector candidate_k | 15 |
| BM25 candidate_k | 15 |
| RRF_K | 60 |
| reranker model | cross-encoder/ms-marco-MiniLM-L6-v2 |
| rerank candidate_k | 15 |
| rerank batch size | 16 |
| dedup overlap threshold | 0.30 |
| similarity threshold | 0 (gate disabled) |
| final top_k | 5 |

---

## Q1 — Where is the GPT model defined?

Expected: `model.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | model.py | 1-34 | 5 | 1 | 0.9373 |
| 2 | sample.py | 40-67 | 4 | 2 | 0.2764 |
| 3 | README.md | 1-21 | 2 | 3 | 0.1940 |
| 4 | train.py | 155-177 | 10 | 4 | 0.0844 |
| 5 | README.md | 180-208 | 7 | 5 | 0.0525 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **4**

---

## Q2 — How is self-attention implemented?

Expected: `model.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | model.py | 65-98 | 2 | 1 | 0.9446 |
| 2 | model.py | 49-66 | 1 | 2 | 0.5997 |
| 3 | model.py | 30-51 | 3 | 3 | 0.0673 |
| 4 | model.py | 1-34 | 4 | 4 | 0.0003 |
| 5 | model.py | 91-128 | 5 | 5 | 0.0001 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **1**

---

## Q3 — Where is the training loop implemented?

Expected: `train.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | README.md | 206-223 | 4 | 1 | 0.0117 |
| 2 | train.py | 321-336 | 1 | 2 | 0.0018 |
| 3 | README.md | 180-208 | 9 | 3 | 0.0013 |
| 4 | README.md | 1-21 | 3 | 4 | 0.0004 |
| 5 | train.py | 225-257 | 11 | 5 | 0.0003 |

- Expected Rank: `train.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **2**

**Regression note:** in Hybrid (no reranker), `train.py` was rank 1. The reranker demoted it to rank 2 and promoted `README.md 206-223` to rank 1.

---

## Q4 — How are configuration values overridden?

Expected: `configurator.py` (primary), `train.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | model.py | 205-224 | 3 | 1 | 0.2678 |
| 2 | configurator.py | 1-33 | 1 | 2 | 0.0084 |
| 3 | model.py | 223-243 | 8 | 3 | 0.0001 |
| 4 | train.py | 57-77 | 13 | 4 | 0.0001 |
| 5 | train.py | 174-198 | 12 | 5 | 0.0000 |

- Expected Rank: `configurator.py` = **2**, `train.py` = **4**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3**

**Regression note:** in Hybrid (no reranker), `configurator.py` was rank 1. The reranker demoted it to rank 2 and incorrectly promoted `model.py 205-224` (`from_pretrained` dropout override) to rank 1.

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

Expected: `model.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | README.md | 1-21 | 1 | 1 | 0.9758 |
| 2 | model.py | 205-224 | 2 | 2 | 0.7118 |
| 3 | sample.py | 40-67 | 11 | 3 | 0.5448 |
| 4 | train.py | 174-198 | 3 | 4 | 0.5302 |
| 5 | config/train_gpt2.py | 1-25 | 9 | 5 | 0.4300 |

- Expected Rank: `model.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **5**

**Q5 verdict:** `model.py` is still rank 2; the reranker did **not** promote it above `README.md 1-21`.

---

## Q6 — How does text generation work?

Expected: `model.py`, `sample.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | README.md | 157-165 | 3 | 1 | 0.0001 |
| 2 | sample.py | 64-89 | 5 | 2 | 0.0001 |
| 3 | data/openwebtext/prepare.py | 27-60 | 6 | 3 | 0.0001 |
| 4 | data/shakespeare_char/prepare.py | 1-32 | 2 | 4 | 0.0000 |
| 5 | data/shakespeare/prepare.py | 1-33 | 10 | 5 | 0.0000 |

- Expected Rank: `sample.py` = **2** (`model.py` not in final Top-5)
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **5**

### Q6 key ranks

| Chunk | RRF Rank | Reranker Rank | Final Rank |
| ----- | -------: | ------------: | ---------: |
| model.py 292-313 (`generate()`) | 14 | 9 | N/A (not in Top-5) |
| sample.py 64-89 (generation loop) | 5 | 2 | 2 |

**Q6 verdict:** `sample.py 64-89` is retained in the final Top-5 (rank 2). `model.py 292-313` (`generate()`) was **not** promoted into Top-3; it only reached reranker rank 9 and stayed out of the final Top-5.

---

## Overall Metrics

| Metric | Hybrid (no reranker) | Hybrid + Reranker |
| ------ | -------------------: | ----------------: |
| Hit@1 | 66.7% | 33.3% |
| Hit@3 | 83.3% | 100% |
| Hit@5 | 100% | 100% |

- Hit@1: **2 / 6 = 33.3%**
- Hit@3: **6 / 6 = 100%**
- Hit@5: **6 / 6 = 100%**
- Average Unique File Count: (4+1+2+3+5+5) / 6 = **3.33**

### Change vs Hybrid

| Metric | Hybrid | Reranker | Change |
| ------ | -----: | -------: | -----: |
| Hit@1 | 66.7% | 33.3% | **-33.3 pp (regression)** |
| Hit@3 | 83.3% | 100% | **+16.7 pp (improvement)** |
| Hit@5 | 100% | 100% | 0.0 pp |

---

## Regression Check

- **Q3 regressed at Hit@1:** `train.py` fell from rank 1 (Hybrid) to rank 2 (Reranker); `README.md 206-223` took rank 1.
- **Q4 regressed at Hit@1:** `configurator.py` fell from rank 1 (Hybrid) to rank 2 (Reranker); `model.py 205-224` incorrectly took rank 1.
- Q1/Q2/Q5/Q6 kept the same Hit@1 status (Q5 still rank 2, Q6 still not top 1).
- No question improved its Hit@1 vs Hybrid; Q3 and Q4 lost Hit@1.

---

## Analysis

- The MS MARCO CrossEncoder is trained for natural-language passage ranking. On code-focused questions it tends to prefer README prose and semantically related but not exactly correct chunks (e.g., `model.py 205-224` for Q4, README chunks for Q3/Q5/Q6).
- The reranker scores for many code chunks are extremely close to 0 (e.g., Q3/Q6 all below 0.02), which makes the ranking brittle and sensitive to small differences.
- The reranker improved **recall/diversity** (Hit@3 100%, Hit@5 100%, unique file count 3.33) at the cost of **Top-1 precision** (Hit@1 dropped to 33.3%).

---

## Conclusion

- **Should the reranker be kept?** Not with the current MS MARCO model for code retrieval. It improves Hit@3/Hit@5 but severely hurts Hit@1 (33.3% vs 66.7%). Recommend not keeping this exact configuration as the default until a code-aware reranker is used.
- **Q5:** `model.py` stayed at rank 2 (not promoted to rank 1).
- **Q6:** `sample.py 64-89` retained (rank 2), but `model.py generate()` was not promoted into Top-3.
