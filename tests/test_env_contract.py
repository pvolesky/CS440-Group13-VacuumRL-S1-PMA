"""Environment contract tests. PLACEHOLDERS: un-skip as Phase 1 (env.py) is implemented.

Contract source: .claude/skills/environment-spec/SKILL.md and docs/environment.md.
Each test body states what to assert; replace `raise NotImplementedError` with real checks.
"""
import pytest

pytestmark = pytest.mark.skip(reason="Phase 1: VacuumGridEnv is not implemented yet")


def test_reset_returns_start_state():
    """reset() returns the cell marked 'start' as a (row, col) tuple."""
    raise NotImplementedError


def test_step_returns_five_tuple():
    """step() -> (next_state, reward, terminated, truncated, info)."""
    raise NotImplementedError


def test_obstacle_blocks_movement():
    """Moving into 'X' leaves the robot in place (provisional blocked_move rule)."""
    raise NotImplementedError


def test_boundary_blocks_movement():
    """Moving off the grid leaves the robot in place."""
    raise NotImplementedError


def test_entering_terminal_cell_terminates():
    """Entering the terminal cell sets terminated=True and truncated=False."""
    raise NotImplementedError


def test_truncation_at_max_episode_steps():
    """After max_episode_steps non-terminal steps: truncated=True, terminated=False."""
    raise NotImplementedError


def test_same_seed_gives_same_trajectory():
    """Two envs with the same seed and actions produce identical trajectories."""
    raise NotImplementedError


def test_info_does_not_leak_model():
    """info must not expose transition probabilities or the reward function."""
    raise NotImplementedError


def test_oracle_matches_documented_semantics():
    """oracle_model() T and R agree with step() on every (state, action) pair."""
    raise NotImplementedError
