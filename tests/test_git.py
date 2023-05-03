"""Test git functions."""
import pytest

from gpt_review._git import _commit


def commit_test() -> None:
    """Test Case for commit wrapper."""
    message = _commit()
    assert message


def test_commit(mock_openai: None, mock_git_commit: None) -> None:
    """Unit test for commit function."""
    commit_test()


@pytest.mark.integration
def test_int_commit(mock_git_commit: None) -> None:
    """Integration test for commit function."""
    commit_test()
