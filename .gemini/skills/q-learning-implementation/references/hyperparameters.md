# Hyperparameters: defaults and sweep suggestions

Defaults live in `configs/default.toml`. This file explains what they mean and how to explore them. It deliberately does not restate the default values, so there is one source of truth.

| Parameter | Config key | Effect | Suggested sweep |
|---|---|---|---|
| Learning rate | `[agent].alpha` | Higher learns faster but is noisier, especially with stochastic transitions | 0.05, 0.1, 0.3, 0.5 |
| Discount | `[agent].gamma` | Lower values make the robot prefer near-term reward; very low values can make the dock look unattractive from far away | 0.9, 0.95, 0.99 |
| Epsilon start/end | `[agent].epsilon_start`, `epsilon_end` | Start high to explore; keep a small floor if the environment may be stochastic | end in 0.0, 0.01, 0.05 |
| Epsilon decay | `[agent].epsilon_decay_episodes` | How fast exploration fades; too fast risks a suboptimal policy that never gets corrected | 200, 500, 1000 |
| Optimistic init | `[agent].optimistic_init` | Positive initial Q-values drive systematic early exploration in deterministic tasks | 0.0 and a value above the best achievable return |
| Episodes | `[training].episodes` | Budget; this grid is small, so convergence should come well before the default | 500, 2000, 10000 |
| Step cost | `[environment].step_cost` | Part of the problem definition, not a tuning knob. Changing it needs a logged decision | n/a |

## Notes

- Sweep one parameter at a time first, with `n_seeds` seeds each, then look at interactions.
- Judge settings by greedy-evaluation return and by the episode at which the greedy policy first matches the oracle policy, not by training return (which includes exploration noise).
- AIMA Ch. 22 discusses the exploration-exploitation tradeoff and GLIE schemes; use it for vocabulary when documenting choices.
