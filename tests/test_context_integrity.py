"""The context scaffolding must stay valid as the repo evolves (same checks as `make validate`)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from _helpers import REPO_ROOT, load_script

validator = load_script("validate_context", "scripts/validate_context.py")


def test_repo_context_is_valid():
    assert validator.validate(REPO_ROOT) == []


def test_validator_detects_oversized_claude_md():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "CLAUDE.md").write_text("line\n" * 200)
        errors = validator.check_claude_md(root)
    assert any("lines" in e for e in errors)


def test_validator_detects_bad_skill_frontmatter():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill = root / ".claude" / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: other\ndescription: x\n---\nbody\n")
        errors = validator.check_skills(root)
    assert any("frontmatter name" in e for e in errors)


def test_validator_detects_route_pointing_at_missing_skill():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ctx = root / ".claude" / "context"
        ctx.mkdir(parents=True)
        (ctx / "a.md").write_text("snippet")
        (ctx / "routes.json").write_text(
            '{"max_chars": 1500, "routes": [{"id": "a", "file": "a.md", "skill": "ghost", "keywords": ["x"]}]}'
        )
        errors = validator.check_routes(root)
    assert any("ghost" in e for e in errors)


def test_validator_flags_yaml_unsafe_description():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill = root / ".claude" / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Use when needed: always\n---\nbody\n")
        errors = validator.check_skills(root)
    assert any("strict YAML" in e for e in errors)
