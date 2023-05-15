import pytest

from gpt_review.repositories.github import GitHubClient


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

        GitHubClient.post_pr_summary(diff)


def test_empty_summary(empty_summary, mock_openai) -> None:
    get_review_test()


@pytest.mark.integration
def test_int_empty_summary(empty_summary) -> None:
    get_review_test()


def test_file_summary(mock_openai, file_summary) -> None:
    get_review_test()


@pytest.mark.integration
def test_int_file_summary(mock_openai, file_summary) -> None:
    get_review_test()
