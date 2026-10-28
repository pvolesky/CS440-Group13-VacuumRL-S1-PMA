TESTING
- `make test` runs pytest; `make validate` checks context integrity.
- Contract tests in tests/ are skipped placeholders until the matching code exists; un-skip them as you implement.
- tests/test_model_free_invariant.py must keep passing.
- Seed everything; no flaky stochastic assertions (fixed seeds or tolerances).
