import pytest

from gpt_review._github import _GitHubClient


def test_get_review(mock_openai) -> None:
    get_review_test()


@pytest.mark.integration
def test_int_get_review() -> None:
    get_review_test()


def get_review_test() -> None:
    """Test get_review."""
    # Load test data from moock.diff
    with open("tests/mock.diff", "r") as f:
        diff = f.read()

        _GitHubClient.post_pr_summary(diff)
