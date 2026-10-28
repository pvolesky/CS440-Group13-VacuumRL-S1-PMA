"""Static guard for hard rule 1: the agent is model-free.

agent.py must not import the environment module nor reference the privileged
oracle or the environment's private T/R methods.
"""
from __future__ import annotations

import ast

from _helpers import REPO_ROOT

AGENT_PATH = REPO_ROOT / "src" / "vacuum_rl" / "agent.py"
FORBIDDEN_NAMES = {"oracle_model", "_transition", "_reward"}


def find_violations(source: str) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[-1] == "env":
                    violations.append(f"imports {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[-1] == "env":
                violations.append(f"imports from {module or '.env'}")
            if any(alias.name == "env" for alias in node.names):
                violations.append("imports env module")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
            violations.append(f"accesses .{node.attr}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            violations.append(f"references {node.id}")
    return violations


def test_agent_module_is_model_free():
    assert find_violations(AGENT_PATH.read_text(encoding="utf-8")) == []


def test_checker_catches_violations():
    bad_samples = [
        "from vacuum_rl.env import VacuumGridEnv",
        "from . import env",
        "from .env import Action",
        "import vacuum_rl.env",
        "x = env.oracle_model()",
        "y = env._reward(s, a, s2)",
    ]
    for source in bad_samples:
        assert find_violations(source), f"should flag: {source}"


def test_checker_allows_clean_code():
    assert find_violations("import numpy as np\n\nclass A:\n    pass\n") == []
