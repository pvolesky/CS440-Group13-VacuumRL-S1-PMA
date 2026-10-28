# vacuum-rl

A vacuum robot that learns to clean a small grid world with **tabular Q-learning**, set up as a repository for **context engineering with Claude Code** using a persistent-memory architecture.

The environment (from the problem statement):

```
[[start, 0, 0, 0],
 [0,     X, 0, 0],
 [0,     0, 0, 0],
 [0,    -1, 0, 10]]
```

The transition function T and reward function R are not available to the agent, so it must learn from interaction. That is exactly the setting Q-learning was designed for (Russell and Norvig, *AIMA* 4th ed., Ch. 22).

> **Current phase: scaffolding.** The context system, memory, tests and placeholders are in place. Q-learning is deliberately **not** implemented yet. See `docs/roadmap.md`.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"      # numpy + pytest
make validate                # context integrity: sizes, skills, routes, memory
make test                    # pytest; contract tests for unbuilt code are skipped
make hook-demo PROMPT="how should I set epsilon"   # preview what the hook injects
```

Requirements: Python 3.11+, Linux (the hook script targets Linux; `python3` must be on the PATH). Open the repo in Claude Code and the hook, skills and `CLAUDE.md` load automatically.

## How the context system works

Three mechanisms, plus a memory directory, each with a different cost profile:

| Mechanism | Location | When it loads | Holds |
|---|---|---|---|
| **CLAUDE.md** | `CLAUDE.md` | Every session | Hard rules, commands, pointers (under 60 lines) |
| **UserPromptSubmit hook** | `.claude/settings.json`, `.claude/hooks/context_router.py`, `.claude/context/` | Every prompt, relevance-gated, at most 1,500 characters | One-line project status plus up to 3 short snippets matched to the prompt by keyword |
| **Skills** | `.claude/skills/<name>/SKILL.md` | When the task matches the skill's description | Longer procedures, checklists, reference material |
| **Memory** | `memory/` | When read (the status line is injected by the hook) | Decisions, open questions, lessons, pending proposals |

Flow for a prompt like "why is my epsilon schedule not converging?":

1. `CLAUDE.md` is already in context (hard rules, including the model-free boundary).
2. The hook matches `epsilon` and `converging`, and injects the status line plus the exploration and debugging snippets. Each names its skill.
3. Claude loads `q-learning-implementation` or `rl-debugging` for the full procedure, and reads `configs/default.toml` for actual values.
4. If something durable is learned, Claude drafts a proposal in `memory/proposals/` for your approval.

Design rationale and limitations: `docs/context-engineering.md`.

## Repository structure

```
vacuum-rl/
├── CLAUDE.md                     Always-on rules and pointers (kept under 60 lines)
├── README.md                     This file
├── Makefile                      test / validate / hook-demo
├── pyproject.toml                Python 3.11+, numpy; dev: pytest
├── configs/
│   └── default.toml              Single source of truth: environment + hyperparameters (PROVISIONAL)
├── docs/
│   ├── environment.md            Cell semantics, dynamics, PEAS, interface contract (PROVISIONAL)
│   ├── context-engineering.md    Why the context system is built this way
│   └── roadmap.md                Phases 0-4
├── memory/                       Persistent project memory
│   ├── project-status.md         One line, injected into every prompt
│   ├── decisions.md              Append-only decision log (D-001 ...)
│   ├── open-questions.md         Unresolved questions with provisional defaults (Q-001 ...)
│   ├── lessons-learned.md        Hard-won findings
│   └── proposals/                Pending memory updates awaiting your approval
├── .claude/
│   ├── settings.json             Registers the UserPromptSubmit hook
│   ├── hooks/
│   │   └── context_router.py     Keyword router; stdlib only; fails open
│   ├── context/
│   │   ├── routes.json           Keywords -> snippet -> skill, plus the character budget
│   │   └── *.md                  Short snippets (11 topics)
│   └── skills/
│       ├── environment-spec/             Define, change, review the environment
│       ├── q-learning-implementation/    Implement and verify tabular Q-learning (+ references/)
│       ├── rl-experiment-protocol/       Seeds, run layout, metrics, honest reporting
│       ├── rl-debugging/                 Layered debugging checklist and symptom table
│       ├── aima-grounding/               AIMA 4e chapter map, notation, citation convention
│       ├── memory-curation/              Propose-then-merge memory workflow
│       └── context-maintenance/          Maintain the context system itself
├── src/vacuum_rl/                Stubs for future work
│   ├── config.py                 Loads configs/default.toml (implemented)
│   ├── env.py                    VacuumGridEnv: owns T and R (stub)
│   ├── agent.py                  QLearningAgent: model-free (stub)
│   ├── train.py                  Training loop (stub)
│   └── evaluate.py               Greedy evaluation (stub)
├── tests/
│   ├── test_hook.py              Hook routing, budget, fail-open behavior (active)
│   ├── test_context_integrity.py Scaffolding stays valid (active)
│   ├── test_model_free_invariant.py  agent.py cannot touch the environment's internals (active)
│   ├── test_config.py            Config sanity (active)
│   ├── test_env_contract.py      Environment contract (skipped placeholders)
│   └── test_agent_contract.py    Agent contract (skipped placeholders)
├── scripts/
│   └── validate_context.py       Size budgets, frontmatter, routes, memory checks
└── experiments/                  Run outputs go in experiments/runs/ (git-ignored)
```

## Provisional assumptions

You asked for general choices that can be refined later. Until you say otherwise, the repo assumes the following. They live in `configs/default.toml`, are explained in `docs/environment.md`, and are tracked as decision D-007 and open questions Q-001 to Q-004.

- `X` is an impassable obstacle; the `-1` cell is a non-terminal penalty; the `10` cell is the terminal dock.
- Deterministic transitions, blocked moves leave the robot in place, step cost -0.04, gamma 0.99.
- Four movement actions; state is `(row, col)`; episodes truncate at 100 steps.

## Working with Claude in this repo

- Ask for what you want in plain language; the hook and skills supply the project context.
- Claude will not implement Q-learning until you ask (see `CLAUDE.md`).
- When something should persist, Claude writes a proposal in `memory/proposals/` and waits for your approval. You can also edit `memory/` files yourself at any time.
- To add a snippet, route or skill, follow `.claude/skills/context-maintenance/SKILL.md`, then run `make validate`.

## Troubleshooting the hook

| Symptom | Try |
|---|---|
| Nothing seems injected | `/hooks` in Claude Code to confirm registration; `echo '{"prompt":"epsilon"}' \| python3 .claude/hooks/context_router.py` |
| Wrong snippets chosen | `make hook-demo PROMPT="..."` shows scores and hits; adjust `routes.json` keywords |
| Context still not surfaced in your client version | `VACUUM_RL_HOOK_OUTPUT=plain` switches to plain-text output |
| Want it off temporarily | `VACUUM_RL_HOOK_DISABLE=1` |

## References

Russell, S. and Norvig, P. *Artificial Intelligence: A Modern Approach*, 4th ed. Ch. 2 (agents and task environments), Ch. 17 (MDPs, value iteration), Ch. 22 (reinforcement learning).
