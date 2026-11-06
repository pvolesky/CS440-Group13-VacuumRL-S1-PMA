---
name: rl-experiment-protocol
description: Protocol for running, recording, and reporting reinforcement-learning experiments in this repo, covering seeds, run directories, metrics, greedy evaluation, and honest reporting of results. Use whenever the user asks to train, evaluate, compare hyperparameters or algorithms, plot learning curves, or summarize results, even if they just say "run it" or "how well does it work".
---

# Experiment protocol

RL results are noisy. A single lucky seed can look like a breakthrough, so this protocol exists to keep conclusions honest and runs reproducible.

## Before running

- Read `configs/default.toml`. Never hard-code values in scripts; override through a copied config file or CLI flags that are recorded in the run directory.
- State the question the run answers in one sentence (for example "does epsilon_decay_episodes=200 reach the oracle policy sooner than 500?").

## Run layout

Each run writes to `experiments/runs/<YYYY-MM-DD>_<name>_<gitsha>/` (git-ignored; the config is what you commit):

- `config.toml`: exact config snapshot, including overrides
- `metrics.csv`: one row per episode: seed, episode, return, length, epsilon, terminated, truncated
- `eval.csv`: one row per evaluation: seed, episode, greedy return, greedy length, success
- `q_table_seed<N>.npy`: final Q-table per seed
- `summary.json`: aggregate numbers used in any write-up

## Seeds and statistics

- Use at least `[training].n_seeds` independent seeds. Derive per-seed generators from one base seed so the whole run is reproducible.
- Report mean and standard deviation (or min/max) across seeds. Never report one seed as "the result".
- Compare configurations on the same seeds.

## Metrics

- **Training return and length** per episode (includes exploration noise; useful for curves, not for ranking).
- **Greedy evaluation** every `eval_every` episodes: epsilon 0, `eval_episodes` episodes, a separate environment instance, no updates. Use this to rank configurations.
- **Policy agreement with the oracle** (value iteration, AIMA Ch. 17) once the oracle exists: fraction of states where the greedy action is optimal, and the first episode at which it reaches 100 percent.
- A success criterion is not yet defined (Q-004). Until it is, say which proxy you used.

## Reporting

- Lead with the question and the answer, then the numbers, then caveats.
- Say what was not tested. Don't extrapolate beyond the seeds and settings you ran.
- Never state a result you did not produce from a run in this repo. If you only reasoned about it, say so.
- If a finding is surprising or a bug was involved, propose a lessons-learned entry (skill `memory-curation`).
