"""Behavioral tests for the UserPromptSubmit hook (.claude/hooks/context_router.py)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from _helpers import REPO_ROOT, hook_context, load_script, run_hook

router = load_script("context_router", ".claude/hooks/context_router.py")


def _included_ids(prompt: str) -> list[str]:
    _, included, _ = router.build_context(prompt, REPO_ROOT)
    return [m.route["id"] for m in included]


def test_output_is_valid_hook_json():
    result = run_hook(json.dumps({"prompt": "set epsilon", "hook_event_name": "UserPromptSubmit"}))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "UserPromptSubmit"
    assert isinstance(out["additionalContext"], str) and out["additionalContext"]


def test_status_line_always_injected():
    text = hook_context("hello there")
    assert "Status:" in text


def test_unrelated_prompt_gets_status_only():
    assert _included_ids("what is a good name for a pet goldfish") == []


def test_prompts_route_to_expected_topics():
    cases = {
        "how should I set epsilon for exploration": "exploration",
        "implement the q-table update rule": "q-learning",
        "the wall at (1,1) should block movement": "environment",
        "what should the step cost and gamma be": "rewards",
        "my training diverges and the values explode": "debugging",
        "cite AIMA for value iteration": "aima",
        "record this decision": "memory",
        "add a new hook route": "context-system",
    }
    for prompt, expected in cases.items():
        assert expected in _included_ids(prompt), f"{prompt!r} should include route {expected!r}"


def test_budget_and_route_limits_hold_for_greedy_prompt():
    prompt = (
        "environment grid wall reward gamma q-learning epsilon train seed debug test "
        "memory decision hook skill aima mdp repo readme"
    )
    cfg = router.load_routes(REPO_ROOT)
    text, included, _ = router.build_context(prompt, REPO_ROOT)
    assert len(text) <= cfg["max_chars"]
    assert len(included) <= cfg["max_routes"]


def test_included_snippets_name_their_skill():
    text = hook_context("how do I tune epsilon")
    assert "skill `q-learning-implementation`" in text


def test_keyword_matching_allows_suffixes_but_not_mid_word():
    assert router._pattern("reward").search("the rewards are odd")
    assert not router._pattern("test").search("the contest ended")


def test_fail_open_on_garbage_stdin():
    result = run_hook("this is not json")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_fail_open_when_project_files_are_missing():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_hook(json.dumps({"prompt": "epsilon"}), project_dir=Path(tmp))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_disable_switch_produces_no_output():
    result = run_hook(json.dumps({"prompt": "epsilon"}), env_extra={"VACUUM_RL_HOOK_DISABLE": "1"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_plain_output_mode_is_not_json():
    result = run_hook(json.dumps({"prompt": "epsilon"}), env_extra={"VACUUM_RL_HOOK_OUTPUT": "plain"})
    assert result.returncode == 0
    assert result.stdout.startswith(router.HEADER)


def test_shared_skill_pointer_is_not_repeated():
    text = hook_context("set epsilon for q-learning")
    assert text.count("skill `q-learning-implementation`") == 1
