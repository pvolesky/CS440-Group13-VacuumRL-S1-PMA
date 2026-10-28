---
name: context-maintenance
description: How to maintain and extend this repo's context-engineering system itself, including CLAUDE.md, the UserPromptSubmit hook and its routes, the injected snippets, skills, and size budgets. Use when adding or editing a skill, hook route, or snippet, when CLAUDE.md is growing, when the hook injects too much, too little, or the wrong thing, or when the user asks about context, token budget, or how the hook, skills and memory fit together.
---

# Maintaining the context system

The goal is the smallest amount of always-on context that keeps Claude correct, with everything else loaded only when relevant. Each layer has a job and a budget.

## Layers and budgets

| Layer | Loaded | Budget | Holds |
|---|---|---|---|
| `CLAUDE.md` | every session | under 60 lines | Hard rules, commands, where things live |
| Hook output | every prompt | 1,500 characters total | Status line plus up to 3 matched snippets |
| Snippets (`.claude/context/*.md`) | when matched | 450 characters each (validator limit) | Summaries and pointers |
| Skills (`.claude/skills/*/SKILL.md`) | when the task matches the description | under 500 lines; use `references/` for more | Procedures and checklists |
| `docs/`, `memory/`, `configs/` | when read | none | Facts, decisions, values |

## Placement rule of thumb

- Needed on nearly every task and tiny: `CLAUDE.md`.
- A reminder that helps when a topic comes up: snippet.
- A multi-step procedure or checklist: skill.
- A fact that may change: config or docs, and everything else points at it. Duplicated numbers go stale silently.

## Add a hook route

1. Write `.claude/context/<id>.md` (at most 450 characters; summarize and point at a skill or doc).
2. Add an entry to `.claude/context/routes.json`: `id`, `file`, `skill` (or `null`), `priority`, `keywords`.
3. Choose keywords that are specific. Matching is case-insensitive at a word start and allows suffixes, so `test` matches `testing`. Avoid short stems that match unrelated words (`ci` matches `cite`).
4. Run `make validate`, then `make hook-demo PROMPT="a realistic prompt"` and a few prompts that should not match.

## Add a skill

1. Create `.claude/skills/<name>/SKILL.md` with frontmatter `name` (must equal the directory name) and a one-line `description`.
2. Keep the description a single line with no `: ` or ` #` inside it (strict YAML parsers reject those in unquoted values, and the skill would fail to load). `make validate` checks this. Put "when to use" in the description, not the body. Be specific about trigger situations and slightly pushy, because skills tend to under-trigger.
3. Explain why a step matters instead of shouting rules. Prefer imperative form.
4. Move bulky detail into `references/` and say when to read each file.
5. Mention the skill in the relevant `routes.json` entry and, if always relevant, in `CLAUDE.md`'s skill list.
6. Run `make validate`.

## Diagnose problems

- **Hook injects nothing useful:** `make hook-demo PROMPT="..."` shows scores, hits, skipped routes and character use.
- **Hook seems silent in a session:** test it directly with `echo '{"prompt":"epsilon schedule"}' | python3 .claude/hooks/context_router.py`. Check `/hooks` in Claude Code and that `python3` is on the PATH. If JSON context is not surfaced in your client version, try `VACUUM_RL_HOOK_OUTPUT=plain`.
- **CLAUDE.md bloat:** move the procedure to a skill, the fact to docs, and leave a pointer.
- **Stale context:** search for the value in more than one file; keep the one in `configs/` and replace the rest with pointers.

## Review cadence

At each project phase boundary, reread `CLAUDE.md` and the snippets, delete anything no longer true, and update `memory/project-status.md`.
