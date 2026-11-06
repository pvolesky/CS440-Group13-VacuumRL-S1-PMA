#!/usr/bin/env python3
"""Run pytest after Gemini finishes a code-focused task."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

CODE_TASK_WORDS = (
    "code", "implement", "fix", "debug", "refactor", "edit", "modify",
    "write", "add", "change", "pytest", "test", "lab", "q-learning",
    "agent", "environment",
)
MAX_OUTPUT_CHARS = 5000


def emit(payload: dict[str, Any]) -> None:
    """Write one JSON response for Gemini."""
    sys.stdout.write(json.dumps(payload) + "\n")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        emit({})
        return 0

    prompt = str(event.get("prompt", "")).lower()
    if not any(word in prompt for word in CODE_TASK_WORDS):
        emit({})
        return 0

    root_value = os.environ.get("GEMINI_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    project_root = Path(root_value).resolve()
    stop_hook_active = bool(event.get("stop_hook_active", False))

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=100,
            check=False,
        )
    except subprocess.TimeoutExpired:
        emit({"systemMessage": "The post-agent pytest check timed out after 100 seconds."})
        return 0
    except OSError as exc:
        emit({"systemMessage": f"The post-agent pytest check could not start: {exc}"})
        return 0

    output = (result.stdout + "\n" + result.stderr).strip()

    if "No module named pytest" in output:
        emit({
            "systemMessage":
                "pytest is not installed. Install the project development dependencies, then retry."
        })
        return 0

    if result.returncode == 0:
        emit({"systemMessage": "Post-agent pytest check passed."})
        return 0

    summary = output[-MAX_OUTPUT_CHARS:] or (
        f"pytest exited with status {result.returncode} without output."
    )

    if not stop_hook_active:
        emit({
            "decision": "deny",
            "reason": (
                "The post-agent pytest check failed. Review the failures and fix the code, "
                "then finish the task. The hook allows only one automatic retry.\n\n"
                + summary
            ),
        })
    else:
        emit({
            "systemMessage":
                "pytest still fails after Gemini's one retry. Review this output:\n" + summary
        })

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
