# vacuum-rl

A vacuum robot that learns to clean a small grid world with **tabular Q-learning**, set up as a repository for **context engineering with Gemini Code** using a persistent-memory architecture.

The environment (from the problem statement):

```
[[start, 0, 0, 0],
 [0,     X, 0, 0],
 [0,     0, 0, 0],
 [0,    -1, 0, 10]]
```

The transition function T and reward function R are not available to the agent, so it must learn from interaction. That is exactly the setting Q-learning was designed for (Russell and Norvig, *AIMA* 4th ed., Ch. 22).

> **Current phase: Phase 3 complete (experiments). Phase 4 is indefinitely paused (do not implement until explicitly requested).** All core RL components (environment, tabular Q-learning, greedy evaluation, multi-seed experiments, and test suites) are implemented and verified. See `docs/roadmap.md`.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"      # installs numpy, pytest, and MCP servers
make validate                # context integrity: sizes, skills, routes, memory, settings
make test                    # runs full test suite (all 41 contract and invariant tests)
make hook-demo PROMPT="how should I set epsilon"   # preview what the hook injects
```

Requirements: Python 3.11+, Linux, Node.js (`npx` for GitHub MCP).

## Running Q-Learning Manually

### 1. Single Training Run
To run tabular Q-learning with the default hyperparameters defined in `configs/default.toml`:

```bash
python3 -m vacuum_rl.train
```

**Expected output:**
```text
Starting Q-learning training with seed 0...

Training complete! Final evaluation: mean_return=9.94, success_rate=100.0%

==================================================================================
LEARNED Q-TABLE (Expected Future Discounted Rewards for Each State-Action Pair)
==================================================================================
State (r, c)    |    UP (0) | RIGHT (1) |  DOWN (2) |  LEFT (3) | Best Action | max Q(s)
----------------------------------------------------------------------------------
(0, 0) [Start]  |      4.25 |      5.86 |      1.30 |      4.97 | RIGHT       |     5.86
(0, 1)          |      4.64 |      6.52 |      4.70 |      4.11 | RIGHT       |     6.52
(0, 2)          |      5.82 |      5.85 |      7.26 |      4.61 | DOWN        |     7.26
(0, 3)          |      2.40 |      2.43 |      8.00 |      3.26 | DOWN        |     8.00
(1, 0)          |      0.92 |      0.07 |      2.64 |      0.12 | DOWN        |     2.64
(1, 1) [Obstacle] |        -- |        -- |        -- |        -- | --          |       --
(1, 2)          |      5.95 |      8.07 |      7.72 |      6.55 | RIGHT       |     8.07
(1, 3)          |      6.49 |      7.59 |      8.98 |      6.93 | DOWN        |     8.98
(2, 0)          |      0.13 |      4.72 |      0.08 |      0.53 | RIGHT       |     4.72
(2, 1)          |      0.81 |      7.16 |     -0.69 |      0.32 | RIGHT       |     7.16
(2, 2)          |      3.54 |      8.98 |      3.43 |      1.67 | RIGHT       |     8.98
(2, 3)          |      7.21 |      8.47 |      9.99 |      7.45 | DOWN        |     9.99
(3, 0)          |      0.51 |     -0.58 |      0.01 |      0.04 | UP          |     0.51
(3, 1) [Hazard] |      0.00 |      0.00 |      0.00 |      0.00 | Terminal    |     0.00
(3, 2)          |      1.60 |      6.86 |      0.47 |     -0.27 | RIGHT       |     6.86
(3, 3) [Dock]   |      0.00 |      0.00 |      0.00 |      0.00 | Terminal    |     0.00
==================================================================================

LEARNED POLICY & MAXIMUM STATE VALUES V(s) = max_a Q(s, a):
  Policy Grid (^ > v <)                     Value Grid V(s)
    >     >     v     v                5.86     6.52     7.26     8.00
    v     X     >     v                2.64    --        8.07     8.98
    >     >     >     v                4.72     7.16     8.98     9.99
    ^    Haz    >    Dock              0.51     0.00     6.86     0.00
==================================================================================
```

### 2. Multi-Seed Experiments & Sweeps
To run the full Phase 3 experiment suite across 5 independent seeds (seeds 0 through 4) for both the baseline and hyperparameter sweeps:

```bash
python3 scripts/run_experiments.py
```

This runs:
- **`baseline`**: 5 seeds with default parameters ($\alpha = 0.1, \gamma = 0.9, \epsilon_{\text{decay}} = 0.99$)
- **`sweep_epsilon_decay_0.95` & `0.995`**: Exploration decay rate comparisons
- **`sweep_alpha_0.05` & `0.2`**: Learning rate sensitivity comparisons

**Artifacts Generated:**
Outputs are written to `experiments/runs/<date>_<name>_<sha>/` (git-ignored):
- `config.toml`: Frozen configuration snapshot
- `metrics.csv`: Episodic training curves (return, length, $\epsilon$, termination, truncation)
- `eval.csv`: Greedy evaluation checkpoints ($\epsilon = 0$) and value-iteration oracle agreement
- `q_table_seed<N>.npy`: Serialized Q-tables for each seed
- `summary.json`: Mean and standard deviation aggregations across seeds
- `experiments/runs.db`: Relational SQLite database recording all runs and checkpoints (queryable via SQLite MCP)

Detailed analysis and conclusions are documented in [`experiments/findings.md`](experiments/findings.md).

## How the context system works

The repository combines five mechanisms, each with a different cost and visibility profile:

| Mechanism | Location | When it loads | Holds |
|---|---|---|---|
| **GEMINI.md** | `GEMINI.md` | Every session | Hard rules, commands, pointers (under 60 lines) |
| **BeforeAgent hook** | `.gemini/settings.json`, `.gemini/hooks/context_router.py`, `.gemini/context/` | Every prompt, relevance-gated, at most 1,500 characters | One-line project status plus up to 3 short snippets matched to the prompt by keyword |
| **AfterAgent hook** | `.gemini/settings.json`, `.gemini/hooks/run_tests_after_agent.py` | After code tasks | Runs `pytest -q` automatically and provides failure feedback to Gemini |
| **MCP Servers** | `.agents/mcp_config.json` | On-demand tool calls | External integrations for GitHub, local SQLite experiment tracking, and web fetch |
| **Skills** | `.gemini/skills/<name>/SKILL.md` | When the task matches the skill's description | Longer procedures, checklists, reference material |
| **Memory** | `memory/` | When read (the status line is injected by the hook) | Decisions, open questions, lessons, pending proposals |

Flow for a prompt like "why is my epsilon schedule not converging?":

1. `GEMINI.md` is already in context (hard rules, including the model-free boundary).
2. The `BeforeAgent` hook matches `epsilon` and `converging`, and injects the status line plus the exploration and debugging snippets. Each names its skill.
3. Gemini loads `q-learning-implementation` or `rl-debugging` for the full procedure, and reads `configs/default.toml` for actual values.
4. If code is modified, the `AfterAgent` hook automatically executes `pytest -q` to catch regressions.
5. If something durable is learned, Gemini drafts a proposal in `memory/proposals/` for your approval.

Design rationale and limitations: `docs/context-engineering.md`.

## Repository structure

```
vacuum-rl/
├── GEMINI.md                     Always-on rules and pointers (kept under 60 lines)
├── README.md                     This file
├── Makefile                      test / validate / hook-demo
├── pyproject.toml                Python 3.11+, numpy; dev: pytest, mcp-server-sqlite, mcp-server-fetch
├── configs/
│   └── default.toml              Single source of truth: environment + hyperparameters (Decision D-009)
├── docs/
│   ├── environment.md            Cell semantics, dynamics, PEAS, interface contract (Decision D-009)
│   ├── context-engineering.md    Why the context system is built this way
│   └── roadmap.md                Phases 0-4
├── memory/                       Persistent project memory
│   ├── project-status.md         One line, injected into every prompt
│   ├── decisions.md              Append-only decision log (D-001 ... D-009)
│   ├── open-questions.md         Unresolved questions with provisional defaults (Q-001 ... Q-005)
│   ├── lessons-learned.md        Hard-won findings
│   └── proposals/                Pending memory updates awaiting your approval
├── .agents/
│   └── mcp_config.json           Workspace Model Context Protocol configuration (github, sqlite, fetch)
├── .gemini/
│   ├── settings.json             Registers BeforeAgent context router and AfterAgent test runner
│   ├── hooks/
│   │   ├── context_router.py     Keyword router; stdlib only; fails open
│   │   └── run_tests_after_agent.py  Automated pytest verification after code tasks
│   ├── context/
│   │   ├── routes.json           Keywords -> snippet -> skill, plus character budget
│   │   └── *.md                  Short snippets (11 topics)
│   └── skills/
│       ├── environment-spec/             Define, change, review the environment
│       ├── q-learning-implementation/    Implement and verify tabular Q-learning (+ references/)
│       ├── rl-experiment-protocol/       Seeds, run layout, metrics, honest reporting
│       ├── rl-debugging/                 Layered debugging checklist and symptom table
│       ├── aima-grounding/               AIMA 4e chapter map, notation, citation convention
│       ├── memory-curation/              Propose-then-merge memory workflow
│       └── context-maintenance/          Maintain the context system itself
├── src/vacuum_rl/                Core reinforcement learning package
│   ├── config.py                 Loads configs/default.toml (implemented)
│   ├── env.py                    VacuumGridEnv: owns T and R; test-only oracle (implemented)
│   ├── agent.py                  QLearningAgent: model-free tabular Q-learning (implemented)
│   ├── train.py                  Training loop and CLI runner (implemented)
│   └── evaluate.py               Greedy evaluation (implemented)
├── tests/
│   ├── test_hook.py              Hook routing, budget, fail-open behavior (active)
│   ├── test_context_integrity.py Scaffolding stays valid (active)
│   ├── test_model_free_invariant.py  agent.py cannot touch the environment's internals (active)
│   ├── test_config.py            Config sanity (active)
│   ├── test_env_contract.py      Environment contract and dynamics (active)
│   └── test_agent_contract.py    Agent contract, updates, and oracle agreement (active)
├── scripts/
│   ├── validate_context.py       Size budgets, frontmatter, routes, memory, settings checks
│   └── run_experiments.py        Phase 3 multi-seed experiment and sweep runner
└── experiments/                  Run outputs go in experiments/runs/ and runs.db (git-ignored)
    └── findings.md               Empirical analysis and sweep findings report
```

## Environment semantics & hyperparameters (D-009)

The environment semantics and learning hyperparameters are finalized in `configs/default.toml`, documented in `docs/environment.md`, and tracked under decision **D-009** (resolving questions Q-001 through Q-004):

- **Grid Cells:**
  - `start` at `(0, 0)`: Initial agent position.
  - `X` at `(1, 1)`: Impassable obstacle (wall/furniture).
  - `-1` at `(3, 1)`: Terminal hazard (hole/fire) with -1 penalty.
  - `10` at `(3, 3)`: Terminal charging dock with +10 reward.
- **Agent Dynamics:** Four movement actions (UP, RIGHT, DOWN, LEFT); state is `(row, col)`; deterministic transitions (`slip_probability = 0.0`); blocked moves leave the robot in place.
- **Reward Structure:** Per-step living cost `step_cost = -0.01`.
- **Hyperparameters:**
  - Learning rate $\alpha = 0.1$
  - Discount factor $\gamma = 0.9$
  - Exploration schedule: $\epsilon_{start} = 1.0$, multiplicative exponential decay factor $0.99$ per episode, down to an $\epsilon_{min} = 0.01$ floor.
  - Truncation limit: $100$ steps per episode.
- **Evaluation Criteria:** $\ge 95\%$ success rate over 20 evaluation episodes with $\epsilon = \epsilon_{min}$ (optimal shortest path: 6 steps, return $+9.94$).

## Model Context Protocol (MCP)

Workspace MCP servers are configured in `.agents/mcp_config.json`:

1. **GitHub MCP (`@modelcontextprotocol/server-github`):**
   - Enables browsing repository PRs, commits, branches, and issues.
   - Uses `${GITHUB_PERSONAL_ACCESS_TOKEN}` from your environment so credentials are never hardcoded or tracked in Git.
   - Configure in your terminal: `export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."`.
2. **SQLite MCP (`mcp-server-sqlite`):**
   - Connects to `experiments/runs.db` (git-ignored) for logging and querying RL episode returns, training seeds, and hyperparameter sweeps.
3. **Fetch MCP (`mcp-server-fetch`):**
   - Allows the agent to fetch documentation, API specifications, and web references directly into context.

## Gemini hooks

Configured in `.gemini/settings.json`:
- **`BeforeAgent`:** Runs `.gemini/hooks/context_router.py`. Injects the current status line and task-matched snippets into Gemini's prompt under a 1,500-character cap.
- **`AfterAgent`:** Runs `.gemini/hooks/run_tests_after_agent.py`. Automatically runs `pytest -q` after code tasks and feeds test failures back to Gemini for self-correction.

## Working with Gemini in this repo

- Ask for what you want in plain language; the hooks and skills supply the project context.
- Gemini will not implement Q-learning until you ask (see `GEMINI.md`).
- When something should persist, Gemini writes a proposal in `memory/proposals/` and waits for your approval. You can also edit `memory/` files yourself at any time.
- To add a snippet, route or skill, follow `.gemini/skills/context-maintenance/SKILL.md`, then run `make validate`.

## Troubleshooting the hooks

| Symptom | Try |
|---|---|
| Nothing seems injected | `/hooks` in Gemini Code to confirm registration; `echo '{"prompt":"epsilon"}' \| python3 .gemini/hooks/context_router.py` |
| Wrong snippets chosen | `make hook-demo PROMPT="..."` shows scores and hits; adjust `routes.json` keywords |
| Context still not surfaced in your client version | `VACUUM_RL_HOOK_OUTPUT=plain` switches to plain-text output |
| Want it off temporarily | `VACUUM_RL_HOOK_DISABLE=1` |

## References

Russell, S. and Norvig, P. *Artificial Intelligence: A Modern Approach*, 4th ed. Ch. 2 (agents and task environments), Ch. 17 (MDPs, value iteration), Ch. 22 (reinforcement learning).
