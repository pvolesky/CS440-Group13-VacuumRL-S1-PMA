ENVIRONMENT (provisional; truth lives in configs/default.toml + docs/environment.md)
- 4x4 grid: start (0,0), obstacle X (1,1), -1 cell (3,1), dock +10 (3,3).
- Env owns T and R. Agent sees only reset(seed) and step(action) -> (next_state, reward, terminated, truncated, info).
- Terminal, hazard, slip and step-cost semantics are unconfirmed: memory/open-questions.md Q-001..Q-003.
