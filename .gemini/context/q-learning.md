Q-LEARNING (not implemented yet; implement only when the user asks)
- Off-policy TD: Q(s,a) += alpha * (r + gamma * max_a' Q(s',a') - Q(s,a)).
- No bootstrap when `terminated`; DO bootstrap when only `truncated`.
- The agent stays model-free: no access to T or R.
- Verify against a value-iteration oracle (AIMA Ch. 17) in tests only.
