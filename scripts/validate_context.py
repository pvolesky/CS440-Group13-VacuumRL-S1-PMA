#!/usr/bin/env python3
"""Validate the context-engineering scaffolding. Standard library only.

Checks: CLAUDE.md size, status line, hook registration, routes and snippets,
skill frontmatter and references, memory files and ID uniqueness.
Exit status 1 if any check fails. Run via `make validate`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CLAUDE_MD_MAX_LINES = 60
CLAUDE_MD_MAX_CHARS = 4000
SNIPPET_MAX_CHARS = 450
STATUS_MAX_CHARS = 200
SKILL_BODY_MAX_LINES = 500
SKILL_DESC_MAX_CHARS = 1024
MIN_HOOK_BUDGET = 400

REQUIRED_MEMORY_FILES = [
    "README.md",
    "project-status.md",
    "decisions.md",
    "open-questions.md",
    "lessons-learned.md",
    "proposals/README.md",
    "proposals/_template.md",
]


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    """Parse simple `key: value` YAML frontmatter. Returns (fields | None, body)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            fields: dict[str, str] = {}
            for raw in lines[1:i]:
                if ":" in raw and not raw.startswith((" ", "\t")):
                    key, _, value = raw.partition(":")
                    fields[key.strip()] = value.strip()
            return fields, "\n".join(lines[i + 1 :])
    return None, text


def check_claude_md(root: Path) -> list[str]:
    path = root / "CLAUDE.md"
    if not path.exists():
        return ["CLAUDE.md is missing"]
    text = path.read_text(encoding="utf-8")
    errors = []
    n_lines = len(text.splitlines())
    if n_lines > CLAUDE_MD_MAX_LINES:
        errors.append(f"CLAUDE.md has {n_lines} lines (max {CLAUDE_MD_MAX_LINES}); move detail to skills or docs")
    if len(text) > CLAUDE_MD_MAX_CHARS:
        errors.append(f"CLAUDE.md has {len(text)} chars (max {CLAUDE_MD_MAX_CHARS})")
    return errors


def check_status(root: Path) -> list[str]:
    path = root / "memory" / "project-status.md"
    if not path.exists():
        return ["memory/project-status.md is missing"]
    content = [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith(("#", "<!--"))
    ]
    if not content:
        return ["memory/project-status.md has no status line (first non-heading line is injected)"]
    if len(content[0]) > STATUS_MAX_CHARS:
        return [f"status line is {len(content[0])} chars (max {STATUS_MAX_CHARS})"]
    return []


def skill_names(root: Path) -> set[str]:
    base = root / ".claude" / "skills"
    return {p.name for p in base.iterdir() if p.is_dir()} if base.exists() else set()


def check_routes(root: Path) -> list[str]:
    path = root / ".claude" / "context" / "routes.json"
    if not path.exists():
        return [".claude/context/routes.json is missing"]
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"routes.json is not valid JSON: {exc}"]

    errors: list[str] = []
    max_chars = cfg.get("max_chars")
    if not isinstance(max_chars, int) or max_chars < MIN_HOOK_BUDGET:
        errors.append(f"routes.json max_chars must be an int >= {MIN_HOOK_BUDGET}")
    skills = skill_names(root)
    seen: set[str] = set()
    for route in cfg.get("routes", []):
        rid = route.get("id", "<missing id>")
        if rid in seen:
            errors.append(f"route id '{rid}' is duplicated")
        seen.add(rid)
        snippet = root / ".claude" / "context" / str(route.get("file", ""))
        if not snippet.is_file():
            errors.append(f"route '{rid}': snippet file '{route.get('file')}' not found")
        else:
            size = len(snippet.read_text(encoding="utf-8").strip())
            if size > SNIPPET_MAX_CHARS:
                errors.append(f"route '{rid}': snippet is {size} chars (max {SNIPPET_MAX_CHARS})")
        keywords = route.get("keywords")
        if not keywords or not all(isinstance(k, str) and k.strip() for k in keywords):
            errors.append(f"route '{rid}': keywords must be a non-empty list of non-empty strings")
        skill = route.get("skill")
        if skill is not None and skill not in skills:
            errors.append(f"route '{rid}': skill '{skill}' does not exist in .claude/skills/")
    return errors


def check_skills(root: Path) -> list[str]:
    base = root / ".claude" / "skills"
    if not base.exists():
        return [".claude/skills/ is missing"]
    errors: list[str] = []
    for skill_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        md = skill_dir / "SKILL.md"
        if not md.exists():
            errors.append(f"skill '{skill_dir.name}': SKILL.md is missing")
            continue
        fields, body = parse_frontmatter(md.read_text(encoding="utf-8"))
        if fields is None:
            errors.append(f"skill '{skill_dir.name}': missing or malformed YAML frontmatter")
            continue
        if fields.get("name") != skill_dir.name:
            errors.append(f"skill '{skill_dir.name}': frontmatter name is '{fields.get('name')}'")
        desc = fields.get("description", "")
        if not desc:
            errors.append(f"skill '{skill_dir.name}': description is empty")
        elif not desc.startswith(('"', "'")) and (": " in desc or " #" in desc):
            errors.append(
                f"skill '{skill_dir.name}': unquoted description contains ': ' or ' #', which strict YAML "
                "parsers reject; reword it or quote the whole value"
            )
        elif len(desc) > SKILL_DESC_MAX_CHARS:
            errors.append(f"skill '{skill_dir.name}': description is {len(desc)} chars (max {SKILL_DESC_MAX_CHARS})")
        n_lines = len(body.splitlines())
        if n_lines > SKILL_BODY_MAX_LINES:
            errors.append(f"skill '{skill_dir.name}': body has {n_lines} lines (max {SKILL_BODY_MAX_LINES}); use references/")
        refs = skill_dir / "references"
        if refs.is_dir():
            for ref in sorted(refs.iterdir()):
                if ref.is_file() and ref.name not in body:
                    errors.append(f"skill '{skill_dir.name}': references/{ref.name} is never mentioned in SKILL.md")
    return errors


def check_settings(root: Path) -> list[str]:
    path = root / ".claude" / "settings.json"
    if not path.exists():
        return [".claude/settings.json is missing"]
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f".claude/settings.json is not valid JSON: {exc}"]
    entries = cfg.get("hooks", {}).get("UserPromptSubmit", [])
    commands = [h.get("command", "") for e in entries for h in e.get("hooks", [])]
    if not any("context_router.py" in c for c in commands):
        return ["settings.json does not register context_router.py under hooks.UserPromptSubmit"]
    if not (root / ".claude" / "hooks" / "context_router.py").is_file():
        return [".claude/hooks/context_router.py is missing"]
    return []


def check_memory(root: Path) -> list[str]:
    errors = []
    mem = root / "memory"
    for rel in REQUIRED_MEMORY_FILES:
        if not (mem / rel).is_file():
            errors.append(f"memory/{rel} is missing")
    for filename, prefix in (("decisions.md", "D"), ("open-questions.md", "Q"), ("lessons-learned.md", "L")):
        path = mem / filename
        if not path.is_file():
            continue
        ids = re.findall(rf"^## ({prefix}-\d+)\b", path.read_text(encoding="utf-8"), flags=re.M)
        dupes = {i for i in ids if ids.count(i) > 1 and i != f"{prefix}-000"}
        if dupes:
            errors.append(f"memory/{filename}: duplicate IDs {sorted(dupes)}")
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for check in (check_claude_md, check_status, check_settings, check_routes, check_skills, check_memory):
        errors.extend(check(root))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print(f"Context validation FAILED ({len(errors)} problem(s)):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Context validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
