"""Q-learning agent contract tests. PLACEHOLDERS: un-skip as Phase 2 is implemented.

Procedure and hand-computed numbers: .claude/skills/q-learning-implementation/SKILL.md
"""
import pytest

pytestmark = pytest.mark.skip(reason="Phase 2: QLearningAgent is not implemented yet")


def test_update_matches_hand_computation():
    """Q=0, alpha=0.5, gamma=0.9, r=1, max Q(s')=2 -> new Q == 1.4."""
    raise NotImplementedError


def test_terminal_update_ignores_next_state_value():
    """Same setup with terminated=True -> new Q == 0.5."""
    raise NotImplementedError


def test_truncated_transition_still_bootstraps():
    """terminated=False (even if the episode was truncated) uses r + gamma*max Q(s')."""
    raise NotImplementedError


def test_greedy_ties_are_broken_randomly():
    """With equal Q-values, repeated greedy choices cover all tied actions."""
    raise NotImplementedError


def test_same_seed_gives_identical_q_table():
    """Training twice with one seed gives identical Q-tables."""
    raise NotImplementedError


def test_greedy_policy_matches_value_iteration_oracle():
    """After training, greedy policy equals the oracle policy on visited states."""
    raise NotImplementedError
