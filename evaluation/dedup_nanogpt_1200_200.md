# nanoGPT Retrieval Deduplication Evaluation

## Experiment Goal

Verify the new pipeline:

`Question -> Vector Search Top-15 Candidates -> Overlap Deduplication -> Final Top-5 -> DeepSeek`

Focus areas:

1. Do overlapping chunks decrease?
2. Does retrieval diversity improve?
3. Do correct files still survive in Top-K?
4. Does Q6 improve because Top-K slots are freed?
5. Is the overall effect on Hit@K positive or negative?

No re-index was performed. The existing 1200/200 nanoGPT index (73 chunks) was reused.

---

## Configuration

| Item | Value |
| ---- | ----- |
| target repository | ../target_repos/nanoGPT |
| embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| embedding dimension | 384 |
| chunk_size | 1200 |
| chunk_overlap | 200 |
| candidate multiplier | 3 |
| candidate_k | 15 |
| final top_k | 5 |
| dedup overlap threshold | 0.30 |
| similarity gate | disabled for evaluation (`threshold=0`) |
| Chroma collection | repomind (cosine, HNSW) |
| collection size | 73 chunks |

---

## Baseline Metrics

| Metric | Value |
| ------ | ----- |
| Hit@1 | 66.7% |
| Hit@3 | 83.3% |
| Hit@5 | 83.3% |

---

## Q1 — Where is the GPT model defined?

- Expected file: `model.py`
- Dedup removed chunks: **none**

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.4813 | model.py | 1-34 |
| 2 | 0.4606 | README.md | 1-21 |
| 3 | 0.4578 | model.py | 205-224 |
| 4 | 0.4417 | sample.py | 40-67 |
| 5 | 0.4267 | model.py | 223-243 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3** (model.py, README.md, sample.py)
- Candidates before dedup: 15 · Final after dedup: 5

**Analysis:** Correct file stays at rank 1. Dedup removed nothing because the two `model.py` chunks 205-224 and 223-243 only overlap by ~2 lines (ratio ~0.10), below the 0.30 threshold. So `model.py` still occupies 3 of 5 slots and a small overlap remains.

---

## Q2 — How is self-attention implemented?

- Expected file: `model.py`
- Dedup removed chunks: **none**

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.2789 | model.py | 65-98 |
| 2 | 0.1839 | model.py | 49-66 |
| 3 | 0.1733 | model.py | 91-128 |
| 4 | 0.1520 | model.py | 1-34 |
| 5 | 0.1442 | model.py | 30-51 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **1** (all model.py)
- Candidates before dedup: 15 · Final after dedup: 5

**Analysis:** `model.py` is still rank 1, but the final Top-5 is 100% `model.py`. The `CausalSelfAttention` implementation (roughly lines 30-98) is split across chunks 65-98, 49-66, and 30-51; those overlaps (e.g., 49-66 vs 65-98) are ~0.11-0.23, below the 0.30 threshold, so dedup did not fire. The correct Self-Attention context is present but fragmented and low-similarity. DeepSeek still produced a grounded explanation from the retrieved fragments.

---

## Q3 — Where is the training loop implemented?

- Expected file: `train.py`
- Dedup removed chunks: **none**

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.3702 | train.py | 321-336 |
| 2 | 0.3601 | train.py | 57-77 |
| 3 | 0.3312 | README.md | 106-122 |
| 4 | 0.3273 | train.py | 278-299 |
| 5 | 0.3159 | config/train_shakespeare_char.py | 1-37 |

- Expected Rank: `train.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3** (train.py, README.md, config/train_shakespeare_char.py)
- Candidates before dedup: 15 · Final after dedup: 5

**Analysis:** Correct file at rank 1. The three `train.py` chunks are distinct (no overlap), so dedup correctly left them alone. Retrieval quality is good.

---

## Q4 — How are configuration values overridden?

- Expected files: `configurator.py` (primary), `train.py`
- Dedup removed chunks: **1**

| Removed file | Lines | Overlap ratio |
| ------------ | ----- | ------------: |
| configurator.py | 28-47 | 0.30 |

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.4272 | configurator.py | 1-33 |
| 2 | 0.4115 | train.py | 76-96 |
| 3 | 0.1871 | model.py | 205-224 |
| 4 | 0.1825 | model.py | 223-243 |
| 5 | 0.1712 | model.py | 30-51 |

- Expected Rank: `configurator.py` = **1**, `train.py` = **2**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3** (configurator.py, train.py, model.py)
- Candidates before dedup: 15 · Final after dedup: 5

**Analysis:** This is the only question where dedup fired. It removed the overlapping `configurator.py` 28-47 chunk (overlap ratio 0.30 vs 1-33) and kept both `configurator.py` and `train.py` in the top 2. The freed slot went to a `model.py` chunk that is largely irrelevant to config overrides, so diversity (by file count) stayed at 3. A small overlap still remains between `model.py` 205-224 and 223-243.

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

- Expected file: `model.py`
- Dedup removed chunks: **none**

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.6359 | README.md | 1-21 |
| 2 | 0.5099 | model.py | 205-224 |
| 3 | 0.4880 | README.md | 106-122 |
| 4 | 0.4846 | config/train_gpt2.py | 1-25 |
| 5 | 0.4303 | README.md | 157-165 |

- Expected Rank: `model.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3** (README.md, model.py, config/train_gpt2.py)
- Candidates before dedup: 15 · Final after dedup: 5

**Analysis:** Correct file at rank 2. README chunks occupy 3 of 5 slots but are different line ranges (1-21, 106-122, 157-165), so dedup does not remove them. The retrieved `model.py` chunk ends at line 224, so the actual `GPT2LMHeadModel.from_pretrained` weight-copying code remains out of context. DeepSeek's answer is only partially grounded for this reason.

---

## Q6 — How does text generation work? (critical question)

- Expected files: `model.py`, `sample.py`
- Dedup removed chunks: **none**

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.2641 | data/shakespeare_char/readme.md | 1-9 |
| 2 | 0.2562 | data/shakespeare_char/prepare.py | 1-32 |
| 3 | 0.2410 | data/shakespeare/prepare.py | 1-33 |
| 4 | 0.2360 | data/shakespeare/readme.md | 1-9 |
| 5 | 0.2273 | README.md | 18-47 |

- Expected Rank: **N/A** (neither target file in final Top-5)
- Hit@1: ❌  Hit@3: ❌  Hit@5: ❌
- Unique File Count: **5** (all five are different files)
- Candidates before dedup: 15 · Final after dedup: 5

**Top-15 candidate check (extra read-only diagnostic):**

| Candidate rank | Similarity | File | Lines |
| -------------: | ---------: | ---- | ----- |
| 7 | 0.1959 | model.py | 292-313 |
| 12 | 0.1700 | sample.py | 1-23 |
| 15 | 0.1332 | sample.py | 64-89 |

- `model.py` 292-313 contains the `generate()` method.
- `sample.py` 64-89 contains the actual generation loop (`model.generate(...)` + decode).

**Q6 failure stage:** The correct chunks **do enter the Top-15 candidates**, but they rank 7/12/15, so they never reach the final Top-5. Dedup could not help because the Top-5 are five different, non-overlapping irrelevant files; there was nothing to remove. This is a **Vector Retrieval / Ranking failure**, not a Dedup failure.

---

## Overall Metrics

| Metric | Value |
| ------ | ----- |
| Hit@1 | 4 / 6 = 66.7% |
| Hit@3 | 5 / 6 = 83.3% |
| Hit@5 | 5 / 6 = 83.3% |
| Average Unique File Count | (3+1+3+3+3+5) / 6 = 3.0 |
| Total overlapping chunks removed | 1 |

---

## Baseline vs Dedup

| Metric | Baseline | Dedup | Change |
| ------ | -------: | ----: | -----: |
| Hit@1 | 66.7% | 66.7% | 0.0 pp |
| Hit@3 | 83.3% | 83.3% | 0.0 pp |
| Hit@5 | 83.3% | 83.3% | 0.0 pp |

---

## Retrieval Diversity Analysis

- **Did duplicate chunks decrease?** Only one overlapping chunk was removed across all six questions (`configurator.py` 28-47 in Q4). The other known overlaps were below the 0.30 threshold and survived.
- **Did Unique File Count improve?** No meaningful change. Average Unique File Count is 3.0, identical to baseline. Q4 kept 3 unique files but swapped the duplicate `configurator.py` for extra `model.py` chunks.
- **Did a correct result gain a Top-K slot via dedup?** No. In Q4 the freed slot went to an irrelevant `model.py` chunk; in Q6 nothing was removed, so no slot was freed.
- **Is overlap still remaining?** Yes. `model.py` 205-224 / 223-243 persists in Q1 and Q4, and Q2 still has multiple overlapping `model.py` chunks (49-66 / 65-98 and 1-34 / 30-51).

---

## Q6 Failure Analysis

- Verdict: **Dedup did not solve it.**
- `model.py` / `sample.py` **are present in Top-15 candidates** (ranks 7, 12, 15).
- They **do not enter the final Top-5**.
- Failure type: **Vector Recall / Ranking Failure** — the correct chunks rank too low (0.13-0.20 similarity), and the Top-5 contains five different irrelevant files with no overlap for dedup to remove.
- This indicates the next improvement should target retrieval recall (e.g., BM25 + Vector + RRF), not more aggressive dedup.

---

## Conclusion

1. **Is deduplication effective?** Marginally. It only removed one chunk in six questions; most real overlaps fall below the 0.30 threshold and remain.
2. **Should the feature be kept?** Yes, keep it as a safety mechanism, but it is not solving the main retrieval problem at its current threshold.
3. **Did Hit@K improve?** No. Hit@1/3/5 are unchanged (66.7% / 83.3% / 83.3%).
4. **Did retrieval diversity improve?** Not meaningfully; average unique file count is unchanged at 3.0.
5. **Was Q6 solved?** No. Correct chunks are in Top-15 but rank too low to reach Top-5.
6. **Should the next step be Hybrid Retrieval (BM25 + Vector + RRF)?** Yes. The Q6 evidence points to a vector recall/ranking gap, which dedup cannot fix.
