# Open questions

Each entry has a provisional default (what the repo assumes today) and the files to touch when it is resolved.
To resolve: draft a proposal that closes the question, logs a decision, and updates the listed files.

## Q-001: Cell semantics [RESOLVED]
- **Status:** resolved (decision D-009)
- **Resolution:** `X` is impassable obstacle; `-1` terminal hazard (hole/fire) on entry; `10` terminal charging dock.

## Q-002: Dynamics and reward structure [RESOLVED]
- **Status:** resolved (decision D-009)
- **Resolution:** Deterministic transitions, step cost -0.01, gamma 0.9, alpha 0.1, epsilon start 1.0 decaying exponentially at 0.99/episode to floor 0.01, no bump penalty.

## Q-003: Actions and state [RESOLVED]
- **Status:** resolved (decision D-009)
- **Resolution:** Four movement actions (UP, RIGHT, DOWN, LEFT); state is `(row, col)`.

## Q-004: Episode limits and success criteria [RESOLVED]
- **Status:** resolved (decision D-009)
- **Resolution:** 100-step truncation limit. Success criterion: 95% success rate over 20 evaluation episodes with epsilon at floor 0.01. Optimal path is 6 steps with return +9.94.

## Q-005: Hook refinements
- **Question:** Should the hook deduplicate snippets already injected earlier in the session? Is lexical keyword routing good enough?
- **Provisional default:** Stateless keyword routing; every matching prompt re-injects (about 1.5 KB at most).
- **Touches:** `.gemini/hooks/context_router.py`, `docs/context-engineering.md`.
