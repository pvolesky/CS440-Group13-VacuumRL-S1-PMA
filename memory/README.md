# memory/

Persistent project memory: durable facts, decisions and lessons that outlive any single chat session.

| File | Purpose | Who writes it |
|---|---|---|
| `project-status.md` | One-line status injected into every prompt by the hook | Claude may update at the end of a meaningful task and says so; the user can edit anytime |
| `decisions.md` | Append-only decision log (ADR style) | Claude proposes, user approves |
| `open-questions.md` | Unresolved questions with provisional defaults | Claude proposes, user approves |
| `lessons-learned.md` | Hard-won findings (bugs, surprises, what worked) | Claude proposes, user approves |
| `proposals/` | Pending memory updates awaiting approval | Claude drafts |

## Workflow

1. Claude notices something memory-worthy (a user-confirmed fact, a decision with rationale, a recurring bug, an unanswered question).
2. Claude copies `proposals/_template.md` to `proposals/NNNN-short-title.md` and fills it in.
3. The user reviews. Approve (merge into the target file and delete or archive the proposal), edit, or reject.
4. Decisions are never rewritten. A changed decision gets a new entry that supersedes the old one.

Full procedure: `.claude/skills/memory-curation/SKILL.md`.

## What is not memory

Code summaries (read the code), transient task state (use the chat), anything already in `configs/` or `docs/` (link to it instead of copying it).
