# RepoMind nanoGPT Extended Evaluation

## Configuration

- AST-aware Python Chunking (fixed_markdown for .md)
- chunk_size = 1200
- chunk_overlap = 200
- Jina Code Embedding (`jinaai/jina-embeddings-v2-base-code`)
- embedding dimension = 768
- Vector candidate count = 15
- BM25 candidate count = 15
- RRF_K = 60
- Dedup threshold = 0.30
- final top_k = 5
- Reranker = OFF
- similarity threshold = 0 (gate disabled)

## Dataset

- 24 answerable questions (6 baseline + 18 new)
- 4 negative questions (out-of-scope features)
- Question type distribution: location 3, implementation 13, configuration 4, cross-file 4
- Symbol-oriented questions: 13

## Overall File Metrics

- Hit@1 = 22/24 = 91.7%
- Hit@3 = 23/24 = 95.8%
- Hit@5 = 23/24 = 95.8%
- Mean Expected File Rank = 1.25 (missing = 6)

## Overall Symbol Metrics

- Symbol-oriented questions: 13
- Hit@1 = 6/13 = 46.2%
- Hit@3 = 10/13 = 76.9%
- Hit@5 = 10/13 = 76.9%
- Mean Expected Symbol Rank = 2.62 (missing = 6)

## Metrics by Question Type

| Type | Count | Hit@1 | Hit@3 | Hit@5 |
| ---- | ----: | ----: | ----: | ----: |
| location | 3 | 100.0% | 100.0% | 100.0% |
| implementation | 13 | 100.0% | 100.0% | 100.0% |
| configuration | 4 | 75.0% | 75.0% | 75.0% |
| cross-file | 4 | 75.0% | 100.0% | 100.0% |

## Q1-Q24 Results

| ID | Question | Type | Expected File(s) | File Rank | Expected Symbol(s) | Symbol Rank | Final Top-5 |
| -- | -------- | ---- | ---------------- | --------: | ----------------- | ----------: | ----------- |
| Q01 | Where is the GPT model defined? | location | model.py | 1 | GPT | 3 | 1. model.py(GPT.from_pretrained) | 2. model.py | 3. model.py(GPT) | 4. model.py(GPT.from_pretrained) | 5. README.md |
| Q02 | How is self-attention implemented? | implementation | model.py | 1 | CausalSelfAttention.forward, CausalSelfAttention.__init__ | 1 | 1. model.py(CausalSelfAttention.forward) | 2. model.py(CausalSelfAttention.__init__) | 3. model.py(CausalSelfAttention) | 4. model.py(Block.forward) | 5. model.py(GPT.forward) |
| Q03 | Where is the training loop implemented? | location | train.py | 1 | - | - | 1. train.py | 2. train.py | 3. train.py | 4. train.py | 5. train.py |
| Q04 | How are configuration values overridden? | implementation | configurator.py, train.py | 1 | - | - | 1. configurator.py | 2. model.py(GPT.configure_optimizers) | 3. train.py | 4. model.py(GPT.configure_optimizers) | 5. model.py(CausalSelfAttention.forward) |
| Q05 | How does nanoGPT load pretrained GPT-2 weights? | implementation | model.py | 1 | GPT.from_pretrained | 1 | 1. model.py(GPT.from_pretrained) | 2. README.md | 3. model.py(GPT.from_pretrained) | 4. model.py(GPT.from_pretrained) | 5. train.py |
| Q06 | How does text generation work? | implementation | model.py, sample.py | 1 | GPT.generate | N/A | 1. sample.py | 2. README.md | 3. README.md | 4. README.md | 5. data/openwebtext/readme.md |
| Q07 | How is the AdamW optimizer built? | implementation | model.py | 1 | GPT.configure_optimizers | 1 | 1. model.py(GPT.configure_optimizers) | 2. train.py | 3. train.py | 4. train.py | 5. model.py(GPT.configure_optimizers) |
| Q08 | Where are model checkpoints saved and restored? | location | train.py | 1 | - | - | 1. train.py | 2. train.py | 3. model.py(GPT.from_pretrained) | 4. sample.py | 5. config/finetune_shakespeare.py |
| Q09 | How is the learning-rate decay schedule computed? | implementation | train.py | 1 | get_lr | 2 | 1. train.py | 2. train.py(get_lr) | 3. train.py | 4. train.py | 5. model.py(GPT.configure_optimizers) |
| Q10 | How are model parameters initialized? | implementation | model.py | 1 | GPT._init_weights | N/A | 1. model.py(GPT.__init__) | 2. model.py(GPT.get_num_params) | 3. model.py(GPT.from_pretrained) | 4. train.py | 5. model.py(GPT.from_pretrained) |
| Q11 | How are logits and loss computed in a forward pass? | implementation | model.py | 1 | GPT.forward | 1 | 1. model.py(GPT.forward) | 2. train.py(estimate_loss) | 3. model.py(MLP.forward) | 4. model.py(LayerNorm.forward) | 5. train.py |
| Q12 | How does gradient accumulation work during training? | implementation | train.py | 1 | - | - | 1. train.py | 2. train.py | 3. train.py | 4. train.py | 5. train.py |
| Q13 | How does the model shrink its context length? | implementation | model.py | 1 | GPT.crop_block_size | 3 | 1. model.py(GPT.forward) | 2. model.py(GPT.generate) | 3. model.py(GPT.crop_block_size) | 4. README.md | 5. model.py(GPT.__init__) |
| Q14 | How is the training device chosen? | configuration | train.py | 1 | - | - | 1. train.py | 2. train.py | 3. README.md | 4. train.py | 5. bench.py |
| Q15 | How is mixed precision selected? | configuration | train.py | N/A | - | - | 1. model.py(GPT.estimate_mfu) | 2. README.md | 3. config/eval_gpt2_medium.py | 4. model.py(GPT.get_num_params) | 5. config/eval_gpt2_large.py |
| Q16 | How are batch size and gradient accumulation configured? | configuration | train.py | 1 | - | - | 1. train.py | 2. train.py | 3. train.py | 4. train.py | 5. train.py |
| Q17 | Where are model architecture sizes defined? | configuration | model.py, train.py | 1 | GPTConfig | N/A | 1. model.py(GPT.crop_block_size) | 2. train.py | 3. model.py(GPT.from_pretrained) | 4. model.py(GPT.from_pretrained) | 5. train.py |
| Q18 | How does sample.py initialize the model? | cross-file | sample.py | 1 | - | - | 1. sample.py | 2. sample.py | 3. sample.py | 4. model.py(GPT.from_pretrained) | 5. model.py(GPT.__init__) |
| Q19 | How do config files such as train_gpt2.py affect training? | cross-file | config/train_gpt2.py, train.py | 1 | - | - | 1. config/train_gpt2.py | 2. train.py | 3. config/train_shakespeare_char.py | 4. data/shakespeare/prepare.py | 5. train.py |
| Q20 | How is the OpenWebText dataset prepared for training? | cross-file | data/openwebtext/prepare.py, train.py | 2 | - | - | 1. data/openwebtext/readme.md | 2. data/openwebtext/prepare.py | 3. README.md | 4. data/openwebtext/prepare.py | 5. README.md |
| Q21 | How does sample.py encode and decode prompt text? | cross-file | sample.py | 1 | - | - | 1. sample.py | 2. data/shakespeare_char/prepare.py(decode) | 3. data/shakespeare_char/prepare.py | 4. data/shakespeare_char/prepare.py(encode) | 5. README.md |
| Q22 | What does the estimate_loss helper compute? | implementation | train.py | 1 | estimate_loss | 1 | 1. train.py(estimate_loss) | 2. train.py | 3. train.py | 4. bench.py | 5. train.py |
| Q23 | What does the get_batch helper return? | implementation | train.py | 1 | get_batch | 1 | 1. train.py(get_batch) | 2. train.py(estimate_loss) | 3. bench.py | 4. model.py(GPT.get_num_params) | 5. model.py(GPT.generate) |
| Q24 | What is the role of the Block class in the transformer? | implementation | model.py | 1 | Block | 2 | 1. model.py(GPT.crop_block_size) | 2. model.py(Block) | 3. model.py(GPT.__init__) | 4. model.py(LayerNorm) | 5. model.py(CausalSelfAttention) |

## Failure Analysis

### File Hit@5 failures
- Q15 `How is mixed precision selected?`: file vector rank 7, file BM25 rank None, final rank None. Category: Ranking/Vocabulary gap (candidate present in Vector Top-15 but BM25 did not recall it and RRF did not surface it).

### Symbol Hit@5 failures
- Q06 `How does text generation work?` (`GPT.generate`): symbol vector rank None, symbol BM25 rank 3, symbol final rank None.
- Q10 `How are model parameters initialized?` (`GPT._init_weights`): symbol vector rank 7, symbol BM25 rank None, symbol final rank None.
- Q17 `Where are model architecture sizes defined?` (`GPTConfig`): symbol vector rank 3, symbol BM25 rank None, symbol final rank None.

## Hard Cases

### Q6 GPT.generate
- `sample.py` generation loop Final Rank = 1
- `GPT.generate` Vector Rank = N/A (not in Top-15)
- `GPT.generate` BM25 Rank = 3 / 4 (split chunks)
- `GPT.generate` RRF Rank = 8 / 10
- `GPT.generate` Final Rank = N/A
- Classification: Candidate Recall Failure in Vector + Ranking Failure; the symbol is split into two chunks.

### New hard cases
- Q10 `How are model parameters initialized?`
- Q17 `Where are model architecture sizes defined?`

## Negative Question Results

| ID | Question | Top-1 retrieved |
| -- | -------- | --------------- |
| N01 | How does nanoGPT perform reinforcement learning from human feedback? | README.md |
| N02 | Where is the vision transformer model defined? | model.py |
| N03 | How does nanoGPT implement beam search decoding? | README.md |
| N04 | How does nanoGPT use data augmentation such as backtranslation? | README.md |

Correct Refusal Rate: not measured (this run was retrieval-only; DeepSeek generation was not invoked for the negative set).

## Conclusion

1. The previous 6/6 Hit@1=100% was **not** fully maintained on 24 questions: File Hit@1 dropped to 91.7%.
2. File-level retrieval is still fairly stable: Hit@1 91.7%, Hit@3 95.8%, Hit@5 95.8%.
3. Symbol-level retrieval is meaningfully weaker: Hit@1 46.2%, Hit@3 76.9%, Hit@5 76.9%.
4. Hardest question type is `configuration` (75% Hit@1/Hit@3/Hit@5), driven by the mixed-precision question vocabulary gap.
5. Retrieval is close to UI/product-ready for file-level Q&A, but symbol-level recall needs improvement before exposing symbol-grounded answers.
6. Next step: a targeted reranker (symbol-aware) is likely higher value than Query Rewrite; Query Rewrite would mainly help vocabulary-gap questions such as mixed precision.