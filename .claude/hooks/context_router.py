#!/usr/bin/env python3
"""UserPromptSubmit hook: inject short, task-relevant context for vacuum-rl.

Contract (Claude Code hooks):
  stdin   JSON event; we read the "prompt" field.
  stdout  JSON {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                       "additionalContext": "<text>"}}
  exit    always 0 (fail-open): a broken hook must never block the user's prompt.

What it injects, in order, under a hard character budget (routes.json: max_chars):
  1. a header and the one-line project status (memory/project-status.md)
  2. up to max_routes snippets from .claude/context/, chosen by keyword match

Design notes live in docs/context-engineering.md. Standard library only.

Debug:    python3 .claude/hooks/context_router.py --explain "your prompt here"
Disable:  VACUUM_RL_HOOK_DISABLE=1
Plain-text output instead of JSON:  VACUUM_RL_HOOK_OUTPUT=plain
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_CHARS = 1500
DEFAULT_MAX_ROUTES = 3
STATUS_MAX_CHARS = 200
HEADER = "[vacuum-rl context: auto-injected summary; full procedures live in skills]"


@dataclass
class Match:
    route: dict
    score: int
    hits: list[str]


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def load_routes(root: Path) -> dict:
    path = root / ".claude" / "context" / "routes.json"
    return json.loads(path.read_text(encoding="utf-8"))


def read_status(root: Path) -> str:
    """First non-empty line of memory/project-status.md that is not a heading or comment."""
    path = root / "memory" / "project-status.md"
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith(("#", "<!--")):
                return line[:STATUS_MAX_CHARS]
    except OSError:
        pass
    return ""


def _pattern(keyword: str) -> re.Pattern[str]:
    # Left word boundary, then keyword, then any word suffix: "reward" matches "rewards".
    return re.compile(r"(?<!\w)" + re.escape(keyword.lower()) + r"\w*")


def match_routes(prompt: str, routes: list[dict]) -> list[Match]:
    text = prompt.lower()
    matches: list[Match] = []
    for route in routes:
        hits = [kw for kw in route.get("keywords", []) if _pattern(kw).search(text)]
        if hits:
            matches.append(Match(route=route, score=len(hits), hits=hits))
    matches.sort(key=lambda m: (-m.score, m.route.get("priority", 100), m.route["id"]))
    return matches


def render_block(root: Path, route: dict, mentioned_skills: set[str] | None = None) -> str:
    """Snippet text plus a skill pointer (skipped if that skill was already pointed to)."""
    path = root / ".claude" / "context" / route["file"]
    body = path.read_text(encoding="utf-8").strip()
    skill = route.get("skill")
    if skill and (mentioned_skills is None or skill not in mentioned_skills):
        body += f"\nFull procedure: skill `{skill}`."
    return body


def build_context(prompt: str, root: Path) -> tuple[str, list[Match], list[tuple[str, str]]]:
    """Return (context_text, included_matches, skipped[(route_id, reason)])."""
    cfg = load_routes(root)
    max_chars = int(cfg.get("max_chars", DEFAULT_MAX_CHARS))
    max_routes = int(cfg.get("max_routes", DEFAULT_MAX_ROUTES))

    parts = [HEADER]
    status = read_status(root)
    if status:
        parts.append(f"Status: {status}")
    text = "\n".join(parts)

    included: list[Match] = []
    skipped: list[tuple[str, str]] = []
    mentioned_skills: set[str] = set()
    for match in match_routes(prompt, cfg["routes"]):
        rid = match.route["id"]
        if len(included) >= max_routes:
            skipped.append((rid, "max_routes reached"))
            continue
        try:
            block = render_block(root, match.route, mentioned_skills)
        except OSError:
            skipped.append((rid, "snippet file unreadable"))
            continue
        candidate = text + "\n\n" + block
        if len(candidate) > max_chars:
            skipped.append((rid, "over character budget"))
            continue
        text = candidate
        included.append(match)
        if match.route.get("skill"):
            mentioned_skills.add(match.route["skill"])
    return text, included, skipped


def explain(prompt: str, root: Path) -> int:
    text, included, skipped = build_context(prompt, root)
    cfg = load_routes(root)
    print(f"prompt   : {prompt!r}")
    print(f"budget   : {len(text)} / {cfg.get('max_chars', DEFAULT_MAX_CHARS)} chars")
    for m in included:
        print(f"included : {m.route['id']:<14} score={m.score} hits={m.hits}")
    for rid, why in skipped:
        print(f"skipped  : {rid:<14} ({why})")
    if not included and not skipped:
        print("matched  : no routes (status line only)")
    print("---- injected text ----")
    print(text)
    return 0


def emit(context: str) -> None:
    if os.environ.get("VACUUM_RL_HOOK_OUTPUT") == "plain":
        print(context)
        return
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(payload))


def main(argv: list[str]) -> int:
    if os.environ.get("VACUUM_RL_HOOK_DISABLE") == "1":
        return 0
    if len(argv) >= 2 and argv[1] == "--explain":
        return explain(" ".join(argv[2:]), project_root())
    try:
        event = json.load(sys.stdin)
        prompt = event.get("prompt", "") if isinstance(event, dict) else ""
        context, _, _ = build_context(str(prompt), project_root())
    except Exception as exc:  # fail-open by design
        print(f"context_router: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0
    emit(context)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
