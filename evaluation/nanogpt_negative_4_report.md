# RepoMind Negative / Refusal Evaluation

## Stable Baseline

- Git commit: `dcef910752bcb0209b68fd9ae14c8f012dda2925`
- Git tag: `v0.4-retrieval-stable`
- AST-aware Python chunking
- Jina Code Embedding (`jinaai/jina-embeddings-v2-base-code`, 768 dims)
- Vector + BM25 + RRF + Dedup
- Reranker OFF
- threshold = 0
- DeepSeek generation

## Dataset

- Negative question count = 4
- Path: `evaluation/nanogpt_negative_4.json`

## N1

**Question:** How does nanoGPT perform reinforcement learning from human feedback?

**Retrieval Top-5:** README.md 1-21 (top-1, sim 0.6861), README.md 89-108, train.py 28-60, README.md 106-122, train.py 176-199

**DeepSeek answer:** Based on the retrieved repository context, there is **no mention of reinforcement learning from human feedback (RLHF)** in nanoGPT. The context describes nanoGPT as a project focused on training/finetuning medium-sized GPT models and reproducing GPT-2 results, with standard supervised training, AdamW optimizer, DDP, and loading pretrained GPT-2 weights. Since RLHF is not discussed anywhere in the retrieved context, I cannot provide information about how nanoGPT might perform RLHF.

**Classification:** Correct Refusal ✅

**Analysis:** Top-1 is the generic README intro with high vector similarity (0.6861), but the model correctly refused and did not fabricate an RLHF path.


## N2

**Question:** Where is the vision transformer model defined?

**Retrieval Top-5:** model.py 138-148 (GPT.__init__), model.py 1-17 (top-1, sim 0.5815), sample.py 40-67, model.py 223-243, model.py 206-224

**DeepSeek answer:** I cannot find a vision transformer model definition. The context shows a GPT language model implementation in model.py, sample code for loading GPT models, and a from_pretrained method that only supports GPT-2 variants. A vision transformer model is not mentioned or defined in any of the provided sources.

**Classification:** Correct Refusal ✅

**Analysis:** Retrieval returned plausible GPT code (model.py) but DeepSeek did not treat it as evidence for a vision transformer.


## N3

**Question:** How does nanoGPT implement beam search decoding?

**Retrieval Top-5:** README.md 1-21 (top-1, sim 0.5798), sample.py 64-89, model.py 1-17, model.py 206-224, data/shakespeare_char/prepare.py 1-31

**DeepSeek answer:** I cannot find any implementation of beam search decoding in nanoGPT. sample.py uses model.generate() with max_new_tokens, temperature, and top_k, which suggests simpler sampling methods rather than beam search. The actual generate() implementation is not in the provided context. The retrieved context does not contain any information about beam search decoding.

**Classification:** Correct Refusal ✅

**Analysis:** The model correctly noted that generation exists but is not beam search, without asserting an unsupported implementation.


## N4

**Question:** How does nanoGPT use data augmentation such as backtranslation?

**Retrieval Top-5:** README.md 1-21 (final top-1, sim 0.5498), sample.py 40-67 (vector top-1, sim 0.6022), README.md 106-122, model.py 223-243, README.md 219-234

**DeepSeek answer:** There is no mention of data augmentation techniques such as backtranslation in nanoGPT. The context describes a simple repository for training/finetuning GPTs with dataset preparation that tokenizes OpenWebText into train.bin/val.bin. The repository focuses on straightforward supervised language modeling without data augmentation. I cannot provide further details because the retrieved context does not contain information about data augmentation strategies.

**Classification:** Correct Refusal ✅

**Analysis:** Mixed vector/BM25 retrieval (README and sample.py), but the model refused correctly.


## Overall Metrics

| Metric | Value |
| ------ | ----- |
| Correct Refusal | 4 |
| Partial Refusal | 0 |
| Hallucinated Answer | 0 |
| Correct Refusal Rate | 4 / 4 = 100% |

## High-confidence False Retrieval

- Yes, all 4 negative queries produced plausible-looking Top-5 results with top-1 similarity between 0.55 and 0.69 (mostly README/model.py).
- DeepSeek was **not** misled in any of the 4 cases and refused based on grounding.

## Threshold Analysis

- The negatives show that a fixed similarity threshold would be unreliable: negative top-1 similarities (0.55-0.69) overlap with valid positive retrievals, so a numeric cutoff would risk rejecting answerable questions.
- At threshold=0, prompt grounding was sufficient for these 4 cases; no evidence yet supports re-adding a similarity gate.

## Conclusion

1. Prompt grounding is reliable for these 4 negative questions (4/4 correct refusal).
2. No hallucination was observed.
3. Correct Refusal Rate = 100% is acceptable.
4. Yes, the UI should surface an explicit insufficient-context signal when the model cannot ground an answer.
5. Refusal-mechanism engineering is optional for now; the current grounded prompt already handles these negatives.