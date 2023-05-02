"""Test git functions."""
import pytest

from gpt_review._git import _commit_message


def test_diff(mock_openai: None) -> None:
    """Test diff function."""
    diff_test()


@pytest.mark.integration
def test_int_diff() -> None:
    """Test diff function."""
    diff_test()


def diff_test() -> None:
    """Test diff function."""
    message = _commit_message()
    assert message
