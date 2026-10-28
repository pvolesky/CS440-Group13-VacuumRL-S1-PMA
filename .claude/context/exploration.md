EXPLORATION
- Epsilon-greedy with random tie-breaking among max-Q actions.
- Schedule and hyperparameters: configs/default.toml [agent]. Linear decay to a floor is practical but not strictly GLIE (AIMA Ch. 22); say so if results depend on it.
- Evaluate with epsilon=0, separately from training episodes.
