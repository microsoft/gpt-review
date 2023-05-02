"""Test git functions."""
import pytest

from gpt_review._git import _commit


def test_commit(mock_openai: None, mock_git_commit: None) -> None:
    """Test diff function."""
    commit_test()


@pytest.mark.integration
def test_int_commit(mock_git_commit: None) -> None:
    """Test diff function."""
    commit_test()


def commit_test() -> None:
    """Test diff function."""
    message = _commit()
    assert message
