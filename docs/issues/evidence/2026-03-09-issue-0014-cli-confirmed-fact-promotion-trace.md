# 2026-03-09 ISSUE-0014 CLI trace: confirmed identity fact promotion

```bash
python -m pytest -vv tests/test_answer_commit_identity_promotion.py::test_promoted_identity_fact_is_available_as_next_turn_continuity_anchor
```

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /workspace/TestBot/.venv/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: langsmith-0.7.14, anyio-4.12.1
collecting ... collected 1 item

tests/test_answer_commit_identity_promotion.py::test_promoted_identity_fact_is_available_as_next_turn_continuity_anchor PASSED [100%]

============================== 1 passed in 0.31s ===============================
