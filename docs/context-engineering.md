# Context engineering design

This repo uses a persistent-memory architecture so that Claude Code starts every session knowing the project's rules and can pull in more detail exactly when it needs it.

## The layers

```
                       always loaded          CLAUDE.md                (< 60 lines)
 every prompt          hook, relevance-gated  .claude/context/*.md     (<= 1,500 chars per prompt)
 on demand             matched by description .claude/skills/*/SKILL.md (procedures, checklists)
 when read             plain files            docs/, memory/, configs/ (facts, decisions, values)
```

| Layer | Question it answers | Cost |
|---|---|---|
| `CLAUDE.md` | What must Claude always know? | Paid every session |
| `UserPromptSubmit` hook | What is relevant to *this* prompt? | Up to 1,500 characters per prompt |
| Skills | How do I do this kind of task properly? | Only the description until the skill triggers |
| `memory/` | What did we decide, what is open, what did we learn? | Only when read |

## Principles

1. **Small always-on context.** Every always-loaded line competes with the task. `CLAUDE.md` holds hard rules and pointers, nothing else.
2. **Pointers over copies.** Volatile values (rewards, gamma, grid semantics) live in `configs/default.toml` only. Duplicated numbers go stale silently, and stale context is worse than missing context.
3. **Progressive disclosure.** Hook snippets summarize and name the skill with the full procedure. Skills keep long reference material in `references/` and say when to read it.
4. **Fail open.** The hook always exits 0. A broken hook degrades to "no extra context", never to a blocked prompt.
5. **Gated memory.** Claude proposes durable changes; the user approves. Decisions are append-only so history stays auditable.
6. **Mechanical enforcement where possible.** Size budgets, skill frontmatter, route integrity and the model-free boundary are checked by `make validate` and by tests, not by good intentions.
7. **Provisional is a first-class state.** Unconfirmed assumptions are recorded as provisional decisions with matching open questions, so they can be refined without archaeology.

## Hook behavior

1. Read the JSON event from stdin and take `prompt`.
2. Build a header and the one-line status from `memory/project-status.md`.
3. Score each route in `routes.json` by the number of its keywords found in the prompt (word-start match, suffixes allowed). Rank by score, then priority.
4. Add up to `max_routes` snippets while the total stays within `max_chars`. Append a pointer to each snippet's skill once.
5. Print `hookSpecificOutput.additionalContext` JSON and exit 0.

Escape hatches: `VACUUM_RL_HOOK_DISABLE=1`, `VACUUM_RL_HOOK_OUTPUT=plain`, and `--explain "prompt"` for debugging.

## Known limitations (candidates for later refinement)

- Routing is lexical, so paraphrases without a keyword will not match. Extend keywords as you see misses (`make hook-demo`).
- The hook is stateless: the same snippet is re-injected on every matching prompt, up to the cap. Session-level deduplication is tracked as Q-005.
- Hook behavior depends on the installed Claude Code version. If context does not appear, check `/hooks`, run the script by hand, or try plain output mode.

## Why Python for the hook

Linux was the stated target; Python 3 is present nearly everywhere there, handles JSON natively, and is easy to unit test. The script is standard-library only so there is nothing to install for the hook to work.
