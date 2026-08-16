# nanoGPT RAG Baseline Evaluation

## Configuration

| Item | Value |
| ---- | ----- |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Embedding dimension | 384 |
| chunk_size | 1200 |
| chunk_overlap | 200 |
| top_k | 5 |
| similarity threshold | 0.35 (default, unchanged) |
| target repository | ../target_repos/nanoGPT |
| Chroma collection | repomind (cosine, HNSW) |

## Index Statistics

| Metric | Value |
| ------ | ----- |
| Files loaded | 19 |
| Chunks created | 73 |
| Chunks indexed | 73 |
| Embedding shape | (73, 384) |

---

## Q1 — Where is the GPT model defined?

Expected file: `model.py`

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.4813 | model.py | 1-34 |
| 2 | 0.4606 | README.md | 1-21 |
| 3 | 0.4578 | model.py | 205-224 |
| 4 | 0.4417 | sample.py | 40-67 |
| 5 | 0.4267 | model.py | 223-243 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Analysis:** Correct file is top 1. The chunk covers the file header and `LayerNorm`; the `GPT` class body sits in later chunks. Ranks 3 and 5 are overlapping `model.py` chunks (205-224 / 223-243), so a duplicated code region occupies two Top-5 slots.

---

## Q2 — How is self-attention implemented?

Expected file: `model.py`

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.2789 | model.py | 65-98 |
| 2 | 0.1839 | model.py | 49-66 |
| 3 | 0.1733 | model.py | 91-128 |
| 4 | 0.1520 | model.py | 1-34 |
| 5 | 0.1442 | model.py | 30-51 |

- Expected Rank: `model.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Analysis:** The correct file is found, but all similarity scores are low (best 0.2789, below the 0.35 threshold), so the answer was gated and DeepSeek was not called. The `CausalSelfAttention` implementation spans roughly lines 30-98 and was split across multiple chunks; several retrieved chunks overlap (49-66 / 65-98, and 1-34 / 30-51). This is the key stress-test question for the 1200/200 chunking: the file is retrieved, but the code context is fragmented and similarity is weak.

---

## Q3 — Where is the training loop implemented?

Expected file: `train.py`

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.3702 | train.py | 321-336 |
| 2 | 0.3601 | train.py | 57-77 |
| 3 | 0.3312 | README.md | 106-122 |
| 4 | 0.3273 | train.py | 278-299 |
| 5 | 0.3159 | config/train_shakespeare_char.py | 1-37 |

- Expected Rank: `train.py` = **1**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Analysis:** Correct file is top 1. Three different `train.py` chunks cover the config section, the update loop, and the logging/termination tail; they are distinct (no harmful overlap). The `README.md` and config-file results are contextually related to training.

---

## Q4 — How are configuration values overridden?

Expected files: `configurator.py` (primary), `train.py`

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.4272 | configurator.py | 1-33 |
| 2 | 0.4115 | train.py | 76-96 |
| 3 | 0.2964 | configurator.py | 28-47 |
| 4 | 0.1871 | model.py | 205-224 |
| 5 | 0.1825 | model.py | 223-243 |

- Expected Rank: `configurator.py` = **1**, `train.py` = **2**
- Hit@1: ✅  Hit@3: ✅  Hit@5: ✅

**Analysis:** Both expected files appear in the top 2. `configurator.py` 1-33 and 28-47 overlap, so the same region is retrieved twice. Ranks 4-5 are `model.py` `from_pretrained` dropout-override code, which is a different override mechanism and is mostly irrelevant to the CLI configurator question.

---

## Q5 — How does nanoGPT load pretrained GPT-2 weights?

Expected file: `model.py`

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.6359 | README.md | 1-21 |
| 2 | 0.5099 | model.py | 205-224 |
| 3 | 0.4880 | README.md | 106-122 |
| 4 | 0.4846 | config/train_gpt2.py | 1-25 |
| 5 | 0.4303 | README.md | 157-165 |

- Expected Rank: `model.py` = **2**
- Hit@1: ❌  Hit@3: ✅  Hit@5: ✅

**Analysis:** The correct file is retrieved at rank 2, but the top result is a generic README intro that does not explain weight loading. README chunks occupy 3 of the 5 slots. The retrieved `model.py` chunk ends at line 224, while the actual `GPT2LMHeadModel.from_pretrained` loading code continues after line 224, so the key code context is incomplete.

---

## Q6 — How does text generation work?

Expected files: `model.py`, `sample.py`

| Rank | Similarity | File | Lines |
| ---- | ---------: | ---- | ----- |
| 1 | 0.2641 | data/shakespeare_char/readme.md | 1-9 |
| 2 | 0.2562 | data/shakespeare_char/prepare.py | 1-32 |
| 3 | 0.2410 | data/shakespeare/prepare.py | 1-33 |
| 4 | 0.2360 | data/shakespeare/readme.md | 1-9 |
| 5 | 0.2273 | README.md | 18-47 |

- Expected Rank: **N/A** (neither target file retrieved)
- Hit@1: ❌  Hit@3: ❌  Hit@5: ❌

**Analysis:** Complete retrieval miss. Neither `model.py` (`generate` method) nor `sample.py` appeared. All five results are dataset-preparation or README chunks, and the best similarity (0.2641) is below the threshold, so the answer was gated. This is the worst-performing question.

---

## Overall Metrics

| Metric | Score | Percentage |
| ------ | ----- | ---------- |
| Hit@1 | 4 / 6 | 66.7% |
| Hit@3 | 5 / 6 | 83.3% |
| Hit@5 | 5 / 6 | 83.3% |

---

## Retrieval Problems

- **Overlapping chunks detected:** Q1 (`model.py` 205-224 / 223-243), Q2 (`model.py` 49-66 / 65-98 and 1-34 / 30-51), Q4 (`configurator.py` 1-33 / 28-47). Overlap duplicates code across Top-5 slots.
- **Duplicated / single-file concentration:** Q2 returns only `model.py`; Q5 returns 3 `README.md` chunks. Top-K diversity is poor in several cases.
- **Irrelevant retrieval:** Q6 is dominated by `data/shakespeare*` preparation files that have nothing to do with text generation.
- **Fragmented code context:** Q5's weight-loading code is cut off at line 224; Q2's self-attention code is spread across multiple chunks.
- **Semantic dilution / low similarities:** Code chunks frequently score ~0.15-0.28, near or below the 0.35 threshold; the embedding model has a query-code semantic gap for behavioral questions.

---

## Conclusion

`chunk_size=1200 / chunk_overlap=200` works as a baseline for file-location questions (Q1, Q3, Q4 all Hit@1), but it is weak for behavioral code questions: Q2 was retrieved but gated by the threshold, and Q6 was a complete miss. Top-1 is also README-biased in Q5. Considering the priority criteria (recall, rank, context completeness, retrieval diversity, duplicate chunks), 1200/200 is acceptable to keep as the RepoMind v0.1 baseline only with the caveats above. Per instruction, no alternative chunk sizes were tested in this round.
