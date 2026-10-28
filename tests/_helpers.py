"""Shared test helpers (no pytest dependency so scripts can be loaded anywhere)."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "context_router.py"


def load_script(name: str, relative_path: str) -> ModuleType:
    """Import a script that lives outside the package (hook, validator)."""
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_hook(stdin_text: str, env_extra: dict[str, str] | None = None, project_dir: Path | None = None):
    """Run the hook exactly as Claude Code would: a subprocess with JSON on stdin."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("VACUUM_RL_")}
    env["CLAUDE_PROJECT_DIR"] = str(project_dir or REPO_ROOT)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=stdin_text,
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


def hook_context(prompt: str) -> str:
    """Return the additionalContext the hook emits for a prompt."""
    result = run_hook(json.dumps({"prompt": prompt, "hook_event_name": "UserPromptSubmit"}))
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
