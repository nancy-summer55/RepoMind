# Learning MVP Manual Evaluation Template

## Question

- Eval ID:
- Repository: nanoGPT
- Question:
- Type: overview / feature / concept / configuration / negative
- Expected files:
- Expected symbols:
- Negative expected: yes / no
- Evaluator:
- Date:

## Retrieval Result

- Top-K returned: 0 / 1 / 2 / 3 / 4 / 5
- Expected file present: yes / no / not applicable
- Expected file best rank:
- Expected symbol present: yes / no / not applicable
- Expected symbol best rank:
- Source roles shown: yes / no
- Relevance reasons shown: yes / no
- Notes:

| Rank | File | Lines | Symbol | Source Role | Relevant? | Notes |
| ---- | ---- | ----- | ------ | ----------- | --------- | ----- |
| 1 | | | | | yes / partial / no | |
| 2 | | | | | yes / partial / no | |
| 3 | | | | | yes / partial / no | |
| 4 | | | | | yes / partial / no | |
| 5 | | | | | yes / partial / no | |

## Answer Grounding

- Uses only retrieved sources: yes / partial / no
- Cites repository facts with `[Source N]`: yes / partial / no
- Cites correct sources for key claims: yes / partial / no
- Avoids invented files/classes/functions/config/runtime behavior: yes / no
- Clearly states evidence gaps when needed: yes / no / not applicable
- Problematic claims:
- Notes:

## Learning Usefulness

- Directly answers the question: 0 / 1 / 2 / 3
- Explains implementation or concept clearly: 0 / 1 / 2 / 3
- Points to useful files or symbols: 0 / 1 / 2 / 3
- Helps a newcomer decide what to read next: 0 / 1 / 2 / 3
- Overall usefulness score: 0 / 1 / 2 / 3
- Notes:

## Follow-Up Quality

- Exactly 3 follow-ups shown: yes / no
- Follow-ups are non-empty and distinct: yes / no
- Follow-ups are grounded in source path or symbol: yes / partial / no
- Follow-ups match the question intent: yes / partial / no
- At least one follow-up is actionable: yes / no
- Best follow-up:
- Weak follow-up:
- Notes:

## Refusal Check

- Refusal expected: yes / no
- Refusal shown: yes / no
- Refusal is explicit and understandable: yes / partial / no / not applicable
- Refusal avoids hallucinated implementation details: yes / no / not applicable
- For answerable questions, refusal is not over-triggered: yes / no / not applicable
- Notes:

## Failure Classification

Check all that apply:

- [ ] No failure
- [ ] Retrieval missed expected file
- [ ] Retrieval missed expected symbol
- [ ] Source role mislabeled
- [ ] Answer omitted important retrieved evidence
- [ ] Answer cited wrong source
- [ ] Answer made unsupported claim
- [ ] Answer structure was hard to use
- [ ] Follow-ups were generic
- [ ] Follow-ups were misleading
- [ ] Refusal should have happened but did not
- [ ] Refusal happened but question was answerable
- [ ] UI display issue
- [ ] Other:

## Final Judgment

- Pass / Fail / Needs review:
- Severity if failed: low / medium / high
- One-sentence judgment:
- Recommended fix:
