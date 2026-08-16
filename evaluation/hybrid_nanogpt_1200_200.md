# nanoGPT Hybrid Retrieval Evaluation

## Experiment Goal

Evaluate the upgraded pipeline:

`Question -> Vector Search Top-15 + BM25 Search Top-15 -> RRF Fusion -> Deduplication -> Final Top-5 -> DeepSeek`

Focus: does BM25 + RRF improve recall / ranking / diversity compared with the Vector-only baseline and the Vector + Dedup version?

No re-index was performed; the existing nanoGPT 1200/200 index (73 chunks) was reused.

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
| final top_k | 5 |
| BM25 tokenizer | code-aware (identifier splitting) + Porter stemming |
| stemming | yes (nltk PorterStemmer) |
| RRF_K | 60 |
| Dedup overlap threshold | 0.30 |
| similarity threshold | 0 (similarity gate disabled) |
| Chroma collection | repomind (cosine, HNSW), 73 chunks |

### Note: minimal code fix during evaluation

`repo_rag.py` crashed on Q5 with `UnicodeEncodeError: 'gbk' codec can't encode character '\xaf'` while printing a retrieved chunk (README 64-84 contains `¯\_(ツ)_/¯`). This is a console-encoding bug, not a retrieval logic bug. Minimal fix applied: `import sys` and, at the start of `main()`:

```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```

No retrieval/embedding/chunking/BM25/RRF/dedup/DeepSeek logic was changed.

---

## Previous Metrics

| Metric | Vector Baseline | Vector + Dedup |
| ------ | --------------: | -------------: |
| Hit@1 | 66.7% | 66.7% |
| Hit@3 | 83.3% | 83.3% |
| Hit@5 | 83.3% | 83.3% |

---

## Q1 — Where is the GPT model defined?

- Expected: `model.py`

### Vector Top-10

| Rank | Similarity | File | Lines |
| ---: | ---------: | ---- | ----- |
| 1 | 0.4813 | model.py | 1-34 |
| 2 | 0.4606 | README.md | 1-21 |
| 3 | 0.4578 | model.py | 205-224 |
| 4 | 0.4417 | sample.py | 40-67 |
| 5 | 0.4267 | model.py | 223-243 |
| 6 | 0.4159 | train.py | 174-198 |
| 7 | 0.4005 | README.md | 64-84 |
| 8 | 0.3984 | README.md | 180-208 |
| 9 | 0.3956 | README.md | 135-159 |
| 10 | 0.3902 | config/finetune_shakespeare.py | 1-25 |

### BM25 Top-10

| Rank | Score | File | Lines |
| ---: | ----: | ---- | ----- |
| 1 | 12.9994 | data/openwebtext/prepare.py | 27-60 |
| 2 | 7.1851 | model.py | 223-243 |
| 3 | 7.1396 | model.py | 205-224 |
| 4 | 6.9557 | sample.py | 40-67 |
| 5 | 6.9157 | train.py | 174-198 |
| 6 | 6.8262 | README.md | 1-21 |
| 7 | 6.7876 | train.py | 155-177 |
| 8 | 6.6259 | model.py | 1-34 |
| 9 | 6.5610 | README.md | 180-208 |
| 10 | 6.5134 | train.py | 129-157 |

### RRF Fused Top-10 (before dedup)

| Rank | File | Lines | Vector Rank | BM25 Rank | RRF Score |
| ---: | ---- | ----- | ----------: | --------: | --------: |
| 1 | model.py | 205-224 | 3 | 3 | 0.031746 |
| 2 | model.py | 223-243 | 5 | 2 | 0.031514 |
| 3 | README.md | 1-21 | 2 | 6 | 0.031281 |
| 4 | sample.py | 40-67 | 4 | 4 | 0.031250 |
| 5 | model.py | 1-34 | 1 | 8 | 0.031099 |
| 6 | train.py | 174-198 | 6 | 5 | 0.030536 |
| 7 | README.md | 180-208 | 8 | 9 | 0.029199 |
| 8 | sample.py | 1-23 | 14 | 14 | 0.027027 |
| 9 | data/openwebtext/prepare.py | 27-60 | None | 1 | 0.016393 |
| 10 | README.md | 64-84 | 7 | None | 0.014925 |

### Final Top-5 (after dedup)

| Rank | File | Lines | Vector Rank | BM25 Rank | Source |
| ---: | ---- | ----- | ----------: | --------: | ------ |
| 1 | model.py | 205-224 | 3 | 3 | Both |
| 2 | model.py | 223-243 | 5 | 2 | Both |
| 3 | README.md | 1-21 | 2 | 6 | Both |
| 4 | sample.py | 40-67 | 4 | 4 | Both |
| 5 | model.py | 1-34 | 1 | 8 | Both |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3**
- Hybrid effect: **Unchanged** (correct file still top 1; RRF moved `model.py 205-224` above `model.py 1-34`, but no Hit@K change)
- Generation grounding: **Grounded**

---

## Q2 — How is self-attention implemented?

- Expected: `model.py`

### Vector Top-10

| Rank | Similarity | File | Lines |
| ---: | ---------: | ---- | ----- |
| 1 | 0.2789 | model.py | 65-98 |
| 2 | 0.1839 | model.py | 49-66 |
| 3 | 0.1733 | model.py | 91-128 |
| 4 | 0.1520 | model.py | 1-34 |
| 5 | 0.1442 | model.py | 30-51 |
| 6 | 0.1382 | README.md | 219-234 |
| 7 | 0.1259 | data/openwebtext/readme.md | 1-15 |
| 8 | 0.1257 | train.py | 298-322 |
| 9 | 0.1236 | README.md | 106-122 |
| 10 | 0.1120 | model.py | 164-187 |

### BM25 Top-10

| Rank | Score | File | Lines |
| ---: | ----: | ---- | ----- |
| 1 | 35.2918 | model.py | 49-66 |
| 2 | 28.7691 | model.py | 65-98 |
| 3 | 26.9374 | model.py | 30-51 |
| 4 | 24.7890 | model.py | 1-34 |
| 5 | 16.1410 | model.py | 91-128 |
| 6 | 12.6037 | data/openwebtext/prepare.py | 1-32 |
| 7 | 7.5285 | train.py | 57-77 |
| 8 | 6.8685 | model.py | 164-187 |
| 9 | 6.8098 | model.py | 186-208 |
| 10 | 6.7343 | model.py | 125-144 |

### RRF Fused Top-10

| Rank | File | Lines | Vector Rank | BM25 Rank | RRF Score |
| ---: | ---- | ----- | ----------: | --------: | --------: |
| 1 | model.py | 65-98 | 1 | 2 | 0.032522 |
| 2 | model.py | 49-66 | 2 | 1 | 0.032522 |
| 3 | model.py | 91-128 | 3 | 5 | 0.031258 |
| 4 | model.py | 30-51 | 5 | 3 | 0.031258 |
| 5 | model.py | 1-34 | 4 | 4 | 0.031250 |
| 6 | model.py | 164-187 | 10 | 8 | 0.028992 |
| 7 | README.md | 219-234 | 6 | None | 0.015152 |
| 8 | data/openwebtext/prepare.py | 1-32 | None | 6 | 0.015152 |
| 9 | data/openwebtext/readme.md | 1-15 | 7 | None | 0.014925 |
| 10 | train.py | 57-77 | None | 7 | 0.014925 |

### Final Top-5

| Rank | File | Lines | Vector Rank | BM25 Rank | Source |
| ---: | ---- | ----- | ----------: | --------: | ------ |
| 1 | model.py | 65-98 | 1 | 2 | Both |
| 2 | model.py | 49-66 | 2 | 1 | Both |
| 3 | model.py | 91-128 | 3 | 5 | Both |
| 4 | model.py | 30-51 | 5 | 3 | Both |
| 5 | model.py | 1-34 | 4 | 4 | Both |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **1**
- Hybrid effect: **Unchanged** (BM25 strongly reinforces `model.py`, but Top-5 remains 100% model.py and still contains overlapping chunks)
- Generation grounding: **Grounded**

---

## Q3 — Where is the training loop implemented?

- Expected: `train.py`

### Vector Top-10

| Rank | Similarity | File | Lines |
| ---: | ---------: | ---- | ----- |
| 1 | 0.3702 | train.py | 321-336 |
| 2 | 0.3601 | train.py | 57-77 |
| 3 | 0.3312 | README.md | 106-122 |
| 4 | 0.3273 | train.py | 278-299 |
| 5 | 0.3159 | config/train_shakespeare_char.py | 1-37 |
| 6 | 0.3143 | README.md | 206-223 |
| 7 | 0.3081 | README.md | 1-21 |
| 8 | 0.3010 | bench.py | 69-99 |
| 9 | 0.2979 | train.py | 253-281 |
| 10 | 0.2963 | config/train_gpt2.py | 1-25 |

### BM25 Top-10

| Rank | Score | File | Lines |
| ---: | ----: | ---- | ----- |
| 1 | 13.5789 | train.py | 321-336 |
| 2 | 12.6685 | README.md | 1-21 |
| 3 | 12.4743 | README.md | 206-223 |
| 4 | 12.3298 | model.py | 49-66 |
| 5 | 12.3020 | train.py | 57-77 |
| 6 | 12.2859 | train.py | 225-257 |
| 7 | 11.8991 | README.md | 180-208 |
| 8 | 9.5073 | model.py | 1-34 |
| 9 | 7.9673 | model.py | 65-98 |
| 10 | 6.2564 | README.md | 44-73 |

### RRF Fused Top-10

| Rank | File | Lines | Vector Rank | BM25 Rank | RRF Score |
| ---: | ---- | ----- | ----------: | --------: | --------: |
| 1 | train.py | 321-336 | 1 | 1 | 0.032787 |
| 2 | train.py | 57-77 | 2 | 5 | 0.031514 |
| 3 | README.md | 1-21 | 7 | 2 | 0.031054 |
| 4 | README.md | 206-223 | 6 | 3 | 0.031025 |
| 5 | README.md | 44-73 | 12 | 10 | 0.028175 |
| 6 | train.py | 155-177 | 11 | 11 | 0.028169 |
| 7 | README.md | 106-122 | 3 | None | 0.015873 |
| 8 | train.py | 278-299 | 4 | None | 0.015625 |
| 9 | model.py | 49-66 | None | 4 | 0.015625 |
| 10 | config/train_shakespeare_char.py | 1-37 | 5 | None | 0.015385 |

### Final Top-5

| Rank | File | Lines | Vector Rank | BM25 Rank | Source |
| ---: | ---- | ----- | ----------: | --------: | ------ |
| 1 | train.py | 321-336 | 1 | 1 | Both |
| 2 | train.py | 57-77 | 2 | 5 | Both |
| 3 | README.md | 1-21 | 7 | 2 | Both |
| 4 | README.md | 206-223 | 6 | 3 | Both |
| 5 | README.md | 44-73 | 12 | 10 | Both |

- Expected Rank: `train.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **2**
- Hybrid effect: **Unchanged** (correct file top 1, but README chunks now occupy 3 slots, slightly reducing diversity vs baseline)
- Generation grounding: **Grounded**

---

## Q4 — How are configuration values overridden?

- Expected: `configurator.py` (primary), `train.py`

### Vector Top-10

| Rank | Similarity | File | Lines |
| ---: | ---------: | ---- | ----- |
| 1 | 0.4272 | configurator.py | 1-33 |
| 2 | 0.4115 | train.py | 76-96 |
| 3 | 0.2964 | configurator.py | 28-47 |
| 4 | 0.1871 | model.py | 205-224 |
| 5 | 0.1825 | model.py | 223-243 |
| 6 | 0.1712 | model.py | 30-51 |
| 7 | 0.1557 | train.py | 278-299 |
| 8 | 0.1481 | train.py | 174-198 |
| 9 | 0.1343 | model.py | 142-166 |
| 10 | 0.1261 | README.md | 135-159 |

### BM25 Top-10

| Rank | Score | File | Lines |
| ---: | ----: | ---- | ----- |
| 1 | 20.8797 | configurator.py | 1-33 |
| 2 | 13.9637 | model.py | 49-66 |
| 3 | 13.5072 | README.md | 44-73 |
| 4 | 13.3725 | model.py | 125-144 |
| 5 | 13.1954 | train.py | 28-60 |
| 6 | 12.7019 | configurator.py | 28-47 |
| 7 | 10.7431 | model.py | 205-224 |
| 8 | 9.6057 | train.py | 57-77 |
| 9 | 5.0476 | model.py | 30-51 |
| 10 | 4.9650 | train.py | 174-198 |

### RRF Fused Top-10

| Rank | File | Lines | Vector Rank | BM25 Rank | RRF Score |
| ---: | ---- | ----- | ----------: | --------: | --------: |
| 1 | configurator.py | 1-33 | 1 | 1 | 0.032787 |
| 2 | configurator.py | 28-47 | 3 | 6 | 0.031025 |
| 3 | model.py | 205-224 | 4 | 7 | 0.030550 |
| 4 | train.py | 76-96 | 2 | 12 | 0.030018 |
| 5 | model.py | 30-51 | 6 | 9 | 0.029644 |
| 6 | train.py | 174-198 | 8 | 10 | 0.028992 |
| 7 | model.py | 49-66 | None | 2 | 0.016129 |
| 8 | README.md | 44-73 | None | 3 | 0.015873 |
| 9 | model.py | 125-144 | None | 4 | 0.015625 |
| 10 | model.py | 223-243 | 5 | None | 0.015385 |

Dedup removed: `configurator.py 28-47` (overlap ratio 0.30).

### Final Top-5

| Rank | File | Lines | Vector Rank | BM25 Rank | Source |
| ---: | ---- | ----- | ----------: | --------: | ------ |
| 1 | configurator.py | 1-33 | 1 | 1 | Both |
| 2 | model.py | 205-224 | 4 | 7 | Both |
| 3 | train.py | 76-96 | 2 | 12 | Both |
| 4 | model.py | 30-51 | 6 | 9 | Both |
| 5 | train.py | 174-198 | 8 | 10 | Both |

- Expected Rank: `configurator.py` = **1**, `train.py` = **3**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3**
- Hybrid effect: **Unchanged** (both expected files kept; duplicate `configurator.py` removed by dedup)
- Generation grounding: **Grounded**

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

- Expected: `model.py`

### Vector Top-10

| Rank | Similarity | File | Lines |
| ---: | ---------: | ---- | ----- |
| 1 | 0.6359 | README.md | 1-21 |
| 2 | 0.5099 | model.py | 205-224 |
| 3 | 0.4880 | README.md | 106-122 |
| 4 | 0.4846 | config/train_gpt2.py | 1-25 |
| 5 | 0.4303 | README.md | 157-165 |
| 6 | 0.4090 | model.py | 1-34 |
| 7 | 0.3969 | README.md | 135-159 |
| 8 | 0.3864 | train.py | 174-198 |
| 9 | 0.3802 | README.md | 64-84 |
| 10 | 0.3801 | config/eval_gpt2_medium.py | 1-8 |

### BM25 Top-10

| Rank | Score | File | Lines |
| ---: | ----: | ---- | ----- |
| 1 | 39.3819 | README.md | 1-21 |
| 2 | 32.1373 | model.py | 205-224 |
| 3 | 27.9831 | train.py | 174-198 |
| 4 | 25.7709 | model.py | 186-208 |
| 5 | 18.2221 | model.py | 125-144 |
| 6 | 18.2173 | sample.py | 40-67 |
| 7 | 17.2962 | README.md | 157-165 |
| 8 | 16.6538 | model.py | 142-166 |
| 9 | 15.3546 | README.md | 64-84 |
| 10 | 14.3720 | model.py | 242-262 |

### RRF Fused Top-10

| Rank | File | Lines | Vector Rank | BM25 Rank | RRF Score |
| ---: | ---- | ----- | ----------: | --------: | --------: |
| 1 | README.md | 1-21 | 1 | 1 | 0.032787 |
| 2 | model.py | 205-224 | 2 | 2 | 0.032258 |
| 3 | train.py | 174-198 | 8 | 3 | 0.030579 |
| 4 | README.md | 157-165 | 5 | 7 | 0.030310 |
| 5 | README.md | 64-84 | 9 | 9 | 0.028986 |
| 6 | model.py | 1-34 | 6 | 15 | 0.028485 |
| 7 | README.md | 106-122 | 3 | None | 0.015873 |
| 8 | config/train_gpt2.py | 1-25 | 4 | None | 0.015625 |
| 9 | model.py | 186-208 | None | 4 | 0.015625 |
| 10 | model.py | 125-144 | None | 5 | 0.015385 |

### Final Top-5

| Rank | File | Lines | Vector Rank | BM25 Rank | Source |
| ---: | ---- | ----- | ----------: | --------: | ------ |
| 1 | README.md | 1-21 | 1 | 1 | Both |
| 2 | model.py | 205-224 | 2 | 2 | Both |
| 3 | train.py | 174-198 | 8 | 3 | Both |
| 4 | README.md | 157-165 | 5 | 7 | Both |
| 5 | README.md | 64-84 | 9 | 9 | Both |

- Expected Rank: `model.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅
- Unique File Count: **3**
- Hybrid effect: **Unchanged** (README bias persists; `model.py` still rank 2)
- Generation grounding: **Partially Grounded** (actual weight-copy body after `model.py` line 224 is not in context)

### Q5 Analysis

1. `model.py` is **not** promoted to rank 1; README 1-21 is rank 1 in both Vector and BM25, so RRF keeps the same order.
2. The `from_pretrained` chunk (`model.py 205-224`) **does** enter final Top-5 (rank 2).
3. BM25 does **not** overcome the README bias here; README 1-21 has the highest BM25 score (39.38) as well.
4. README bias is **not reduced**; 3 of 5 final slots are README chunks.

---

## Q6 — How does text generation work? (critical)

- Expected: `model.py`, `sample.py`

### Vector Top-15 (key expected-file ranks)

| Vector Rank | Similarity | File | Lines |
| ----------: | ---------: | ---- | ----- |
| 7 | 0.1959 | model.py | 292-313 |
| 12 | 0.1700 | sample.py | 1-23 |
| 15 | 0.1332 | sample.py | 64-89 |

### BM25 Top-15 (key expected-file ranks)

| BM25 Rank | Score | File | Lines |
| --------: | ----: | ---- | ----- |
| 1 | 19.4943 | sample.py | 64-89 |
| 12 | 5.6509 | sample.py | 1-23 |
| 13 | 5.6048 | model.py | 292-313 |

### RRF Fused Top-10

| Rank | File | Lines | Vector Rank | BM25 Rank | RRF Score |
| ---: | ---- | ----- | ----------: | --------: | --------: |
| 1 | README.md | 18-47 | 5 | 2 | 0.031514 |
| 2 | data/shakespeare_char/prepare.py | 1-32 | 2 | 9 | 0.030622 |
| 3 | README.md | 157-165 | 6 | 7 | 0.030077 |
| 4 | sample.py | 64-89 | 15 | 1 | 0.029727 |
| 5 | data/openwebtext/readme.md | 1-15 | 10 | 6 | 0.029437 |
| 6 | data/openwebtext/prepare.py | 27-60 | 14 | 5 | 0.028898 |
| 7 | model.py | 292-313 | 7 | 13 | 0.028624 |
| 8 | sample.py | 1-23 | 12 | 12 | 0.027778 |
| 9 | README.md | 106-122 | 11 | 15 | 0.027418 |
| 10 | data/shakespeare_char/readme.md | 1-9 | 1 | None | 0.016393 |

### Final Top-5

| Rank | File | Lines | Vector Rank | BM25 Rank | Source |
| ---: | ---- | ----- | ----------: | --------: | ------ |
| 1 | README.md | 18-47 | 5 | 2 | Both |
| 2 | data/shakespeare_char/prepare.py | 1-32 | 2 | 9 | Both |
| 3 | README.md | 157-165 | 6 | 7 | Both |
| 4 | sample.py | 64-89 | 15 | 1 | Both |
| 5 | data/openwebtext/readme.md | 1-15 | 10 | 6 | Both |

- Expected Rank: `sample.py` = **4** (`model.py` not in final Top-5)
- Hit@1: ❌  Hit@3: ❌  Hit@5: ✅
- Unique File Count: **4**
- Hybrid effect: **Improved** (Hit@5 changed from ❌ to ✅)
- Generation grounding: **Partially Grounded** (explains `sample.py` generation loop, but `model.generate()` internals are not in context)

### Q6 Analysis

- **Vector stage:** `model.py 292-313` rank 7; `sample.py 1-23` rank 12; `sample.py 64-89` rank 15.
- **BM25 stage:** `sample.py 64-89` rank 1 (strong lexical `generate`/`model.generate` signal); `sample.py 1-23` rank 12; `model.py 292-313` rank 13.
- **RRF stage:** `sample.py 64-89` is promoted to RRF rank 4; `model.py 292-313` reaches only RRF rank 7.
- **Final Top-5:** `sample.py 64-89` enters at rank 4; `model.py 292-313` does not enter.
- **Verdict:** `Q6 Hybrid Retrieval Success` (partial). BM25 + RRF recovered the `sample.py` generation loop, turning Hit@5 from ❌ to ✅. However, Hit@1/Hit@3 still fail, and the `model.py generate()` chunk is still not surfaced (BM25 rank 13 / RRF rank 7).

---

## Overall Metrics

| Metric | Value |
| ------ | ----- |
| Hit@1 | 4 / 6 = 66.7% |
| Hit@3 | 5 / 6 = 83.3% |
| Hit@5 | 6 / 6 = 100% |
| Average Unique File Count | (3+1+2+3+3+4) / 6 = 2.67 |
| Total overlapping chunks removed | 1 |

---

## Baseline vs Dedup vs Hybrid

| Metric | Vector Baseline | Vector + Dedup | Hybrid | vs Baseline |
| ------ | --------------: | -------------: | -----: | ----------: |
| Hit@1 | 66.7% | 66.7% | 66.7% | +0.0 pp |
| Hit@3 | 83.3% | 83.3% | 83.3% | +0.0 pp |
| Hit@5 | 83.3% | 83.3% | 100% | +16.7 pp |

---

## BM25 Contribution

- Correct results clearly helped by BM25: **Q6 `sample.py 64-89`** (BM25 rank 1 pulled it from Vector rank 15 into final Top-5).
- BM25 also reinforced correct chunks in Q1/Q2/Q3/Q4 (correct file frequently BM25 rank 1-3).
- Final Top-5 chunks that are **BM25-only** (not in Vector Top-15): **0** across all six questions.
- BM25 on Q5: ineffective at fixing README bias (`README 1-21` is also BM25 rank 1).
- BM25 on Q6: effective for `sample.py` (rank 1), weak for `model.py generate()` (rank 13).
- Lexical noise: BM25 introduced extra README/`model.py` chunks into the fused Top-15, but none reached final Top-5 as BM25-only.

---

## RRF Analysis

- Chunks ranked highly by both retrievers are promoted (e.g., Q2 `model.py 65-98`, Q3 `train.py 321-336`, Q4 `configurator.py 1-33`, Q5 `README 1-21`).
- Vector-only strong results are demoted when BM25 disagrees (e.g., Q6 `data/shakespeare_char/readme.md` Vector rank 1 -> RRF rank 10, out of Top-5). This is what freed a slot for `sample.py`.
- BM25-only strong results are also capped by RRF (e.g., Q1 `data/openwebtext/prepare.py` BM25 rank 1 -> RRF rank 9).
- RRF still lets some irrelevant-but-both-ranked chunks through (Q3/Q5 README chunks).

---

## Retrieval Problems

- Q5 still has strong README bias; `model.py` remains rank 2.
- Q6 Hit@1/Hit@3 still fail; `model.py generate()` is not surfaced (BM25 rank 13 / RRF rank 7).
- Q2 still shows single-file concentration and residual overlapping `model.py` chunks.
- Q3/Q5 README chunks occupy 3 final slots (lexical noise).
- Dedup still only fires once (Q4); residual small overlaps remain in Q1/Q4.

---

## Conclusion

1. **Is Hybrid Retrieval better than the Vector baseline?** Yes, partially — Hit@5 improves from 83.3% to 100%.
2. **Did Hit@1 improve?** No (66.7% unchanged).
3. **Did Hit@3 improve?** No (83.3% unchanged).
4. **Did Hit@5 improve?** Yes (83.3% -> 100%, +16.7 pp).
5. **Did Q5 improve?** No; README bias persists and `model.py` stays at rank 2.
6. **Was Q6 solved?** Partially: Hit@5 changed from ❌ to ✅ (`sample.py` recovered), but Hit@1/Hit@3 still fail and `model.py generate()` remains unsurfaced.
7. **Does BM25 provide valuable lexical recall?** Yes, especially for Q6 (`sample.py` generation loop recovered from Vector rank 15).
8. **Does RRF fuse the two retrievers reasonably?** Yes; it promotes both-ranked chunks and demotes unsupported single-source results, enabling the Q6 gain.
9. **Is dedup still necessary?** Yes, as a safety mechanism, but it is not the main lever at the current threshold.
10. **Should Hybrid Retrieval be kept as RepoMind v0.2?** Yes, recommend keeping it.
11. **Next step recommendation:** **Reranker** first (a cross-encoder can re-rank RRF Top-15 and is most likely to fix Q5/Q6 ranking gaps), followed by **Code Embedding Model** and **AST-aware Chunking**. Query Rewrite is lower priority for this dataset.
