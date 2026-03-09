# 2026-03-09 ISSUE-0014 CLI trace: identity semantic preservation

```bash
python -m pytest -vv tests/test_pipeline_semantic_contracts.py::test_resolve_turn_intent_matches_canonical_intent_resolution_for_identity_followup
```

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /workspace/TestBot/.venv/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: langsmith-0.7.14, anyio-4.12.1
collecting ... collected 1 item

tests/test_pipeline_semantic_contracts.py::test_resolve_turn_intent_matches_canonical_intent_resolution_for_identity_followup PASSED [100%]

============================== 1 passed in 1.12s ===============================
