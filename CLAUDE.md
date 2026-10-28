# vacuum-rl

Tabular Q-learning for a vacuum robot on a small grid world. The agent is model-free: it never gets T or R.
**Current phase: context scaffolding.** Do not implement Q-learning until the user asks. Status: `memory/project-status.md`.

## Hard rules
1. **Model-free boundary.** The environment owns T and R. The agent sees only `reset()` and `step(action)`. Nothing in `src/vacuum_rl/agent.py` may import or read environment internals (enforced by `tests/test_model_free_invariant.py`).
2. **Environment semantics are provisional.** Walls, hazards, rewards, γ, slip and step cost live in `configs/default.toml` and `docs/environment.md`. Read them there; never hard-code or restate them elsewhere.
3. **Don't invent project facts.** Anything unspecified goes into a proposal for `memory/open-questions.md`; ask the user.
4. **Memory writes go through proposals.** Never edit `memory/decisions.md`, `open-questions.md` or `lessons-learned.md` directly. Draft `memory/proposals/NNNN-title.md` and wait for approval (skill `memory-curation`).
5. **Keep always-on context small.** This file stays under 60 lines. Procedures go in skills, facts in docs or config.

## Commands
- `make test` runs pytest
- `make validate` checks context integrity (sizes, skill frontmatter, hook routes)
- `make hook-demo PROMPT="..."` shows what the hook would inject for a prompt

## Where things live
- `src/vacuum_rl/` environment, agent, training and evaluation code (stubs for now)
- `configs/default.toml` single source of truth for environment and hyperparameters
- `docs/` human-readable specs and design rationale
- `memory/` decisions, open questions, lessons, pending proposals, one-line status
- `.claude/context/` short snippets the hook injects; `.claude/skills/` long procedures

## Context system
- This file is always loaded.
- A `UserPromptSubmit` hook (`.claude/hooks/context_router.py`) injects the status line plus up to 3 snippets (at most 1,500 characters) matched to the prompt. Snippets are summaries that name the skill holding the full procedure.
- Before non-trivial work, load the matching skill: `environment-spec`, `q-learning-implementation`, `rl-experiment-protocol`, `rl-debugging`, `aima-grounding`, `memory-curation`, `context-maintenance`.

## Conventions
- Python 3.11+, type hints, numpy. Hooks and scripts are stdlib-only.
- Every stochastic component takes an explicit seed.
- Cite AIMA 4th ed. by chapter (Ch. 2, 17, 22); see `aima-grounding`.
