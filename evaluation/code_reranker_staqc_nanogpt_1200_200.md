# nanoGPT Python Code Reranker Evaluation

## Experiment Goal

Verify whether a lightweight Python Question-Code CrossEncoder (`NamanAgnih0tri/code-reranker-miniLM-staqc`) is better suited to RepoMind than the generic MS MARCO reranker, under the exact same Hybrid retrieval pipeline.

Pipeline:

`Question -> Vector Top-15 + BM25 Top-15 -> RRF -> RRF Top-15 -> Python Code CrossEncoder -> Dedup -> Final Top-5 -> DeepSeek`

Only the reranker model was changed. No re-index was performed (existing nanoGPT 1200/200, 73 chunks reused). BM25 tokenizer was left untouched.

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
| reranker model | NamanAgnih0tri/code-reranker-miniLM-staqc |
| reranker type | standard CrossEncoder (no custom prompt) |
| reranker download size | ~87.6 MB (model.safetensors 86.7 MB) |
| rerank candidate_k | 15 |
| rerank batch size | 4 |
| dedup overlap threshold | 0.30 |
| similarity threshold | 0 (gate disabled) |
| final top_k | 5 |

---

## Q1 — Where is the GPT model defined?

Expected: `model.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | model.py | 1-34 | 5 | 1 | 6.6435 |
| 2 | train.py | 155-177 | 11 | 2 | 6.5869 |
| 3 | README.md | 1-21 | 3 | 3 | 6.5584 |
| 4 | model.py | 205-224 | 1 | 4 | 6.3168 |
| 5 | README.md | 180-208 | 7 | 5 | 6.2197 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q2 — How is self-attention implemented?

Expected: `model.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | model.py | 49-66 | 2 | 1 | 7.6678 |
| 2 | model.py | 65-98 | 1 | 2 | 7.5080 |
| 3 | model.py | 30-51 | 4 | 3 | 7.1389 |
| 4 | data/openwebtext/prepare.py | 1-32 | 8 | 4 | 5.1432 |
| 5 | model.py | 1-34 | 5 | 5 | 3.6632 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

---

## Q3 — Where is the training loop implemented?

Expected: `train.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | README.md | 206-223 | 4 | 1 | 6.9162 |
| 2 | README.md | 180-208 | 12 | 2 | 6.8688 |
| 3 | train.py | 225-257 | 11 | 3 | 6.8191 |
| 4 | README.md | 1-21 | 3 | 4 | 6.7189 |
| 5 | train.py | 321-336 | 1 | 5 | 6.2275 |

- Expected Rank: `train.py` = **3**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅

**Q3 Regression Check:** FAILED. The Code Reranker demoted `train.py` from RRF Rank 1 to Final Rank 3 and promoted `README.md 206-223` to Rank 1 (same failure mode as MS MARCO).

---

## Q4 — How are configuration values overridden?

Expected: `configurator.py` (primary), `train.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | model.py | 205-224 | 3 | 1 | 7.1539 |
| 2 | configurator.py | 1-33 | 1 | 2 | 6.8174 |
| 3 | model.py | 223-243 | 10 | 3 | 5.7477 |
| 4 | train.py | 57-77 | 13 | 5 | 4.7714 |
| 5 | train.py | 174-198 | 6 | 6 | 4.6100 |

- Expected Rank: `configurator.py` = **2**, `train.py` = **4**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅

**Q4 Regression Check:** FAILED. `configurator.py` lost Rank 1 (fell to Rank 2); `model.py 205-224` (`from_pretrained` dropout override) was wrongly promoted to Rank 1 (same failure mode as MS MARCO).

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

Expected: `model.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | README.md | 1-21 | 1 | 1 | 7.9537 |
| 2 | model.py | 205-224 | 2 | 2 | 7.9234 |
| 3 | model.py | 186-208 | 9 | 3 | 7.7952 |
| 4 | config/train_gpt2.py | 1-25 | 8 | 4 | 7.7916 |
| 5 | train.py | 174-198 | 3 | 5 | 7.7884 |

- Expected Rank: `model.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅

**Q5 README Bias Analysis:** `model.py` stayed at Rank 2; the Code Reranker kept `README.md 1-21` at Rank 1 with a slightly higher score (7.9537 vs 7.9234). README bias was not resolved.

---

## Q6 — How does text generation work?

Expected: `model.py`, `sample.py`

| Final Rank | File | Lines | RRF Rank | Reranker Rank | Reranker Score |
| ---: | ---- | ----- | -------: | ------------: | -------------: |
| 1 | sample.py | 64-89 | 4 | 1 | 3.9704 |
| 2 | data/openwebtext/prepare.py | 27-60 | 6 | 2 | 3.7459 |
| 3 | README.md | 157-165 | 3 | 3 | 3.4346 |
| 4 | README.md | 106-122 | 9 | 4 | 1.8420 |
| 5 | data/shakespeare_char/prepare.py | 1-32 | 2 | 5 | 0.4777 |

- Expected Rank: `sample.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

### Q6 Generation Ranking Analysis

| Chunk | RRF Rank | Reranker Rank | Final Rank |
| ----- | -------: | ------------: | ---------: |
| sample.py 64-89 (`model.generate` loop) | 4 | 1 | 1 |
| model.py 292-313 (`generate()` implementation) | 7 | 13 | N/A (not in Top-5) |

- `sample.py 64-89` was promoted from RRF 4 to Final Rank 1 (improvement over Hybrid, where it was Rank 4).
- `model.py 292-313` was **not** promoted into Top-3; the Code Reranker ranked it 13th (score -4.3593), so it stayed out of the final Top-5.

---

## Hit@K

| Metric | Value |
| ------ | ----- |
| Hit@1 | 3 / 6 = 50.0% |
| Hit@3 | 6 / 6 = 100% |
| Hit@5 | 6 / 6 = 100% |

---

## Hybrid vs MS MARCO vs Python Code Reranker

| Pipeline | Hit@1 | Hit@3 | Hit@5 |
| -------- | ----: | ----: | ----: |
| Vector | 66.7% | 83.3% | 83.3% |
| Hybrid (no reranker) | 66.7% | 83.3% | 100% |
| MS MARCO Reranker | 33.3% | 100% | 100% |
| Python Code Reranker | 50.0% | 100% | 100% |

- vs Hybrid: Hit@1 **-16.7 pp** (66.7% -> 50.0%); Hit@3 **+16.7 pp** (83.3% -> 100%); Hit@5 unchanged (100%).
- vs MS MARCO: Hit@1 **+16.7 pp** (33.3% -> 50.0%); Hit@3/Hit@5 same (100%).

---

## Conclusion

- The Python Code Reranker **did not** beat the pure Hybrid baseline on Hit@1 (50.0% vs 66.7%).
- It **improved** over MS MARCO on Hit@1 (50.0% vs 33.3%) and fixed Q1/Q6 Top-1.
- It still caused the same Q3/Q4 Top-1 regressions as MS MARCO (README promoted over `train.py`; `from_pretrained` code promoted over `configurator.py`).
- Q5 README bias was not resolved; `model.py` stayed at Rank 2.
- Q6 `model.py generate()` was not surfaced (Reranker Rank 13, Final N/A).
- **Recommendation:** Do not keep this Python Code Reranker as the default at this stage. It is better than MS MARCO but still below the Hybrid baseline's Hit@1. The current staqc MiniLM reranker's scores are clustered and not code-structure-aware enough for these repository questions.
