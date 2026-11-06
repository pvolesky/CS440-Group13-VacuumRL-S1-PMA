# Roadmap

Phases are intentionally coarse. Update this file and `memory/project-status.md` at each boundary.

| Phase | Goal | Entry skill | Status |
|---|---|---|---|
| 0 | Context scaffolding: GEMINI.md, hook, skills, memory, validation | `context-maintenance` | Done |
| 1 | Implement the environment per `docs/environment.md`; un-skip `tests/test_env_contract.py`; add the test-only oracle | `environment-spec` | Done |
| 2 | Implement tabular Q-learning, training and evaluation; un-skip `tests/test_agent_contract.py`; verify against the value-iteration oracle | `q-learning-implementation` | Done |
| 3 | Experiments: multi-seed runs, hyperparameter sweeps, learning curves, written findings | `rl-experiment-protocol` | Done |
| 4 | Extensions (choose with the user): stochastic slip, dirt state and "suck" action, SARSA or model-based (ADP) comparison, function approximation | `aima-grounding` | Indefinitely paused (do not implement until explicitly requested by user) |

Before Phase 1, resolve or consciously accept the provisional answers to Q-001 to Q-004.
