---
name: memory-curation
description: How to capture, propose, and merge persistent project memory (decisions, open questions, lessons learned, status line) in this repo. Use whenever the user confirms a project fact, makes or changes a decision, an assumption is discovered, a bug or surprise teaches something reusable, a task finishes, or the user says remember, record, log, decide, or update status, even if they don't mention the memory directory.
---

# Memory curation

The `memory/` directory is how the project stays coherent across sessions. Its value depends on being accurate and small, so every write has a gate.

## What deserves memory

| Capture | Where |
|---|---|
| A user-confirmed fact or choice, with the reason | `decisions.md` |
| Something unspecified that affects design, with the assumption currently in use | `open-questions.md` |
| A bug, surprise or finding that would bite again | `lessons-learned.md` |
| Current phase in one line | `project-status.md` |

Skip: code summaries (read the code), transient task state, anything already in `configs/` or `docs/` (link to it instead), and anything you inferred but the user never confirmed (record it as a provisional decision or an open question, labeled as such).

## Propose, then merge

1. Copy `memory/proposals/_template.md` to `memory/proposals/NNNN-short-title.md` (next four-digit number).
2. Fill in the exact entry text in the target file's format, the evidence for it (user-confirmed or inferred), and the other files to update.
3. Tell the user a proposal is waiting and summarize it in one or two sentences. Do not merge yet.
4. After approval: append the entry to the target file, apply any listed config or docs updates, delete the proposal, and update the status line if the phase changed.
5. If the user rejects or edits it, follow their version.

## Rules

- **Append-only decisions.** Never edit an accepted decision. Add a new entry with `Supersedes: D-00X` and mark the old one `superseded`.
- **IDs are stable.** D-, Q-, L- numbers are never reused or renumbered.
- **Resolving a question** means a decision entry plus removing or marking the question resolved, in the same merge.
- **Status line.** `project-status.md` may be updated directly at the end of a meaningful task; say so in your reply. Keep it to one line of at most 200 characters, because the hook injects it into every prompt.
- **Keep entries short.** If an entry needs more than about ten lines, the detail belongs in `docs/` and the entry should link to it.
- **Run `make validate`** after edits to confirm the status line length and file presence.
