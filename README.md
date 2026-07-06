# Eval Delta

> Detect overall and slice-level regressions between paired LLM evaluation runs

## Snapshot

<img src="assets/readme-cover.svg" alt="Eval Delta cover" width="100%" />

| Part | Notes |
| --- | --- |
| Area | model quality |
| Entry | `eval-delta` |
| Main files | .github/, examples/, src/, tests/ |

## Use

```bash
git clone https://github.com/mertefekurt/eval-delta.git
cd eval-delta
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
eval-delta examples/candidate.jsonl
```

## Notes

This project stays useful when the output is easy to read and the setup is easy to throw away after a quick check.
