<img src="assets/readme-cover.svg" alt="Eval Delta cover" width="100%" />

# Eval Delta

Detect overall and slice-level regressions between paired LLM evaluation runs.

![stack](https://img.shields.io/badge/stack-Python-dc2626?style=flat-square) ![python](https://img.shields.io/badge/python-3.11-7c3aed?style=flat-square) ![license](https://img.shields.io/badge/license-MIT-0891b2?style=flat-square) ![ci](https://img.shields.io/badge/ci-GitHub%20Actions-b45309?style=flat-square)

| Question | Answer |
| --- | --- |
| What is it? | A focused Python utility for evaluation work. |
| How does it run? | `eval-delta` |
| Why keep it small? | Easier review, easier tests, fewer moving parts. |

## Command

```bash
python -m pip install -e ".[dev]"
eval-delta examples/candidate.jsonl
```

## Verify

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m eval_delta --help
```
