---
name: q-learning-implementation
description: Step-by-step procedure for implementing and verifying tabular Q-learning (agent, epsilon-greedy exploration, training loop) for the vacuum-robot grid world. Use when the user asks to implement, extend, tune, or review the Q-learning agent, Q-table, update rule, exploration schedule, or training loop, and before writing any code in src/vacuum_rl/agent.py or train.py. Do not start implementing unprompted, since the repo stays in a scaffolding phase until the user says otherwise.
---

# Tabular Q-learning

## Preconditions

- The user has explicitly asked for implementation. Check `memory/project-status.md`.
- Read `configs/default.toml` (`[agent]`, `[training]`) and `memory/open-questions.md`. If an unresolved question changes the design (for example Q-003, a dirt state), ask before building.
- The environment exists and honors the contract in skill `environment-spec`.

## Algorithm (AIMA 4th ed., Ch. 22, temporal-difference Q-learning)

    Q(s,a) <- Q(s,a) + alpha * (target - Q(s,a))
    target = r                            if terminated
    target = r + gamma * max_a' Q(s',a')  otherwise (including truncated)

Q-learning is off-policy: the target uses the greedy next action regardless of which action the behavior policy actually takes next (SARSA, by contrast, uses the action taken). It is model-free: it consumes only observed `(s, a, r, s', terminated)` tuples and never T or R.

## Implementation steps

1. **State indexing.** The agent works on integer state indices produced by the environment's public `encode_state`; the training loop does the conversion. Store Q as a numpy array of shape `(n_states, n_actions)` initialized to `optimistic_init`. Take `n_states` and `n_actions` from the environment's public attributes, never from its private layout data.
2. **Action selection.** Epsilon-greedy. Break ties among maximal Q-values randomly, using the agent's own `np.random.Generator` seeded from config. Argmax tie-breaking by index silently biases early behavior.
3. **Update.** Implement the target above. Pass `terminated` and `truncated` separately; only `terminated` cuts the bootstrap.
4. **Schedules.** Epsilon and alpha come from config. Constant alpha is the pragmatic default for a small grid. Formal convergence needs decaying alpha and infinite visitation of every state-action pair. A linear epsilon decay to a floor is practical but not strictly GLIE (greedy in the limit with infinite exploration); say so in write-ups if it matters.
5. **Training loop** (`train.py`). Per episode: reset with a seed derived from the run seed, step until `terminated or truncated`, update on every step, log return and length, then decay epsilon.
6. **Evaluation** (`evaluate.py`). Greedy policy (epsilon 0), a separate environment instance and seed, no learning updates.
7. **Persistence.** Save the Q-table (`.npy`) and a config snapshot in the run directory (skill `rl-experiment-protocol`).

## Verification required before saying it works

- **Hand-computed update.** With Q(s,a)=0, alpha=0.5, gamma=0.9, r=1, max Q(s',.)=2: the target is 2.8 and the new Q is 1.4. With `terminated=True` the target is 1 and the new Q is 0.5.
- **Truncation.** A truncated (not terminated) transition still bootstraps.
- **Oracle comparison.** Compute Q* by value iteration with the test-only oracle (AIMA Ch. 17). After training, the greedy policy should match the oracle's policy on states the agent visited, and max |Q - Q*| should shrink. Choose tolerances using several seeds, and widen them if the environment is stochastic.
- **Determinism.** The same seed gives an identical Q-table.

## Do not

- Read T, R, or private environment attributes from the agent.
- Tune hyperparameters by eyeballing a single seed.
- Add reward shaping without a logged decision.
- Move to function approximation unless asked (AIMA Ch. 22 generalization is a possible later phase).

Default ranges and sweep suggestions: `references/hyperparameters.md` (read it when tuning).
