CONTEXT SYSTEM
- Layers: GEMINI.md (always) -> hook snippets (.gemini/context + routes.json) -> skills (.gemini/skills) -> docs and memory.
- New route = snippet file + routes.json entry (<=450 chars); then `make validate` and `make hook-demo PROMPT="..."`.
- Prefer pointers over copies; volatile values live only in configs/default.toml.
