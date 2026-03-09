# 2026-03-09 ISSUE-0014 CLI trace: self-reference retrieval activation

```bash
python -m pytest -vv tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage
```

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /workspace/TestBot/.venv/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: langsmith-0.7.14, anyio-4.12.1
collecting ... collected 1 item

tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage PASSED [100%]

============================== 1 passed in 0.31s ===============================
