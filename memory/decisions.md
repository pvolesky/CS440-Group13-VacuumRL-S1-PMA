# Decision log

Append-only. To change a decision, add a new entry with `Supersedes: D-00X` and set the old entry's status to `superseded`.
Status values: `accepted` | `provisional` (works for now, expected to be refined) | `superseded`.

## D-001: Persistent memory architecture
- **Status:** accepted
- **Decision:** Combine `CLAUDE.md` (small, always-on), a `UserPromptSubmit` hook (short, task-relevant snippets), Claude Code Skills (long procedures), and a `memory/` directory (decisions, open questions, lessons).
- **Why:** Always-on context must stay small; relevance-gated and on-demand layers keep the rest available without paying for it every turn. See `docs/context-engineering.md`.

## D-002: Tooling
- **Status:** accepted
- **Decision:** Python 3.11+, numpy, pytest. Config in TOML (stdlib `tomllib`). Hooks and scripts use the standard library only. Hook scripts target Linux.
- **Why:** Minimal dependencies keep the hook fast and robust; TOML avoids a YAML dependency.

## D-003: Hook behavior
- **Status:** accepted
- **Decision:** Keyword routing from `.claude/context/routes.json`, plus a one-line status, under a 1,500-character cap and at most 3 snippets. The hook always exits 0 (fail-open).
- **Why:** A misbehaving hook must never block the user; a hard cap keeps per-turn overhead predictable.

## D-004: Reference text
- **Status:** accepted (user-specified)
- **Decision:** AIMA, 4th edition (Russell and Norvig). Cite by chapter: Ch. 2 (agents, task environments), Ch. 17 (MDPs), Ch. 22 (reinforcement learning).

## D-005: Model-free boundary
- **Status:** accepted
- **Decision:** The environment owns the transition function T and reward function R. The agent sees only `reset()` and `step(action)`. A privileged oracle view of T and R may exist for tests (value-iteration checks) but must never be imported by agent code.
- **Why:** T and R are unavailable by problem statement; this is what makes the problem a Q-learning problem.

## D-006: Memory writes require approval
- **Status:** accepted
- **Decision:** Claude proposes changes to `decisions.md`, `open-questions.md` and `lessons-learned.md` via `memory/proposals/`; the user approves before merge.
- **Why:** Prevents silent drift of project facts and keeps the user in control of what persists.

## D-007: Provisional environment semantics
- **Status:** provisional
- **Decision:** Until the user specifies otherwise: row-major grid with `start` at (0,0); `X` is an impassable obstacle; the `-1` cell is a non-terminal penalty for entering it; the `10` cell is terminal; transitions are deterministic; blocked moves leave the robot in place; per-step cost -0.04; gamma 0.99; four movement actions; state is (row, col); episodes truncate at 100 steps. Values live in `configs/default.toml`.
- **Why:** The user asked for general choices that can be refined later. Open items: Q-001 to Q-004 in `open-questions.md`.

## D-008: Single source of truth for volatile values
- **Status:** accepted
- **Decision:** Environment and hyperparameter values live only in `configs/default.toml`. Docs, snippets and skills point to it instead of restating numbers.
- **Why:** Duplicated numbers go stale silently, and stale context is worse than missing context.
