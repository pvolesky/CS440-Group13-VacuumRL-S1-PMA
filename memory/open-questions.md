# Open questions

Each entry has a provisional default (what the repo assumes today) and the files to touch when it is resolved.
To resolve: draft a proposal that closes the question, logs a decision, and updates the listed files.

## Q-001: Cell semantics
- **Question:** Is `X` an impassable obstacle? Is `-1` a terminal hazard or a penalty the robot can step through? Is `10` terminal (charging dock)?
- **Provisional default:** `X` impassable; `-1` non-terminal penalty on entry; `10` terminal. (D-007)
- **Touches:** `configs/default.toml` [environment], `docs/environment.md`, `tests/test_env_contract.py`.

## Q-002: Dynamics and reward structure
- **Question:** Deterministic or stochastic transitions (e.g. AIMA's 0.8/0.1/0.1 slip model)? Per-step living cost? Discount factor? Penalty for bumping walls?
- **Provisional default:** Deterministic, step cost -0.04, gamma 0.99, no bump penalty, blocked move leaves the robot in place. (D-007)
- **Touches:** `configs/default.toml` [environment] and [agent], `docs/environment.md`.

## Q-003: Actions and state
- **Question:** Movement actions only with state (row, col), or also a "suck" action and per-cell dirt (AIMA vacuum world)?
- **Provisional default:** Four movement actions; position-only state. (D-007)
- **Touches:** `src/vacuum_rl/env.py`, `src/vacuum_rl/agent.py` (state indexing), `docs/environment.md`. A dirt state multiplies the state space; revisit the tabular approach if adopted.

## Q-004: Episode limits and success criteria
- **Question:** Maximum steps per episode? What counts as "solved" (e.g. greedy policy reaches the dock in the optimal number of steps)?
- **Provisional default:** 100-step truncation; no formal success criterion yet.
- **Touches:** `configs/default.toml`, `docs/environment.md`, skill `rl-experiment-protocol`.

## Q-005: Hook refinements
- **Question:** Should the hook deduplicate snippets already injected earlier in the session? Is lexical keyword routing good enough?
- **Provisional default:** Stateless keyword routing; every matching prompt re-injects (about 1.5 KB at most).
- **Touches:** `.claude/hooks/context_router.py`, `docs/context-engineering.md`.
