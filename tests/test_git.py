"""Test git functions."""
import pytest

from gpt_review._git import _commit, _find_git_dir


def commit_test() -> None:
    """Test Case for commit wrapper."""
    message = _commit()
    assert message

    message = _commit(push=True)
    assert message


def test_commit(mock_openai: None, mock_git_commit: None) -> None:
    """Unit test for commit function."""
    commit_test()


@pytest.mark.integration
def test_int_commit(mock_git_commit: None) -> None:
    """Integration test for commit function."""
    commit_test()


@pytest.mark.unit
@pytest.mark.integration
def test_find_git_dir() -> None:
    _find_git_dir(path="tests")

    with pytest.raises(FileNotFoundError):
        _find_git_dir(path="/")
