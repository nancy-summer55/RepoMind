# RepoMind Demo Screenshots

This folder will contain the four demo screenshots below. They are captured
from the running Streamlit app at 1280x720 (desktop), against the indexed
`nanoGPT` test repository.

Each screenshot should be a real capture of the app; do not edit or fake
any content.

## 01-indexed-repository.png

Show the Repository panel after indexing `..\target_repos\nanoGPT`:

- Header: `nanoGPT ● Indexed`
- Repository summary:
  - Files: 19
  - Chunks: 90
  - Chunking: AST
  - Embedding: Jina Code
  - Embedding dim: 768

How to capture:

1. `streamlit run app.py`
2. Enter `..\target_repos\nanoGPT` and click **Index repository**
3. Wait for `Indexed` status and the summary
4. Screenshot the top of the page (header + Repository panel)

## 02-self-attention-answer.png

Ask the primary demo question:

```
How is self-attention implemented?
```

Show:

- A real DeepSeek-grounded answer mentioning `CausalSelfAttention`
- The `[Source N]` citations in the answer
- The Sources inspector with `model.py` / `CausalSelfAttention.forward` /
  `method · lines 52–70`

How to capture:

1. After indexing, ask the question and wait for the answer
2. Screenshot the Chat + Sources columns

## 03-retrieval-debug.png

With the same answer selected, expand **Retrieval details** and show:

- Source (file)
- Symbol
- Lines
- Vector Rank / Vector Similarity
- BM25 Rank / BM25 Score
- RRF Rank / RRF Score
- Chunk strategy

How to capture:

1. Keep the self-attention answer selected
2. Click **Retrieval details** to expand
3. Screenshot the right-hand Sources panel with the debug rows visible

## 04-insufficient-context.png

Use a negative question from `evaluation/nanogpt_negative_4.json`, e.g.:

```
Where is the vision transformer model defined?
```

Show:

- `Insufficient repository context` (accent-soft, non-error state)
- The mis-retrieved Sources that were still returned
- Retrieval Debug still expandable

How to capture:

1. After indexing, ask the negative question and wait for the refusal state
2. Screenshot the Chat (refusal) + Sources columns

## Notes

- Keep the same 1280x720 viewport for all four captures.
- The UI must be in the default MASTER.md theme (light-first, minimal).
- If a capture cannot be produced reliably in the current environment,
  keep this plan and add the PNG only when the app can be screenshotted
  accurately.