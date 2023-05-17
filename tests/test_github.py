import pytest

from gpt_review.repositories.github import GitHubClient


def get_pr_diff_test(starts_with, patch_repo=None, patch_pr=None) -> None:
    """Test the GitHub API call."""
    diff = GitHubClient.get_pr_diff(patch_repo=patch_repo, patch_pr=patch_pr)
    assert diff.startswith(starts_with)


def post_pr_comment_test() -> None:
    """Test the GitHub API call."""
    response = GitHubClient.post_pr_summary("test")
    assert response


@pytest.mark.integration
def test_int_pr_diff(mock_github) -> None:
    """Integration Test for GitHub API diff call."""
    get_pr_diff_test("diff --git a/README.md b/README.md", "microsoft/gpt-review", 1)


def test_pr_diff(mock_openai, mock_github) -> None:
    """Unit Test for GitHub API diff call."""
    get_pr_diff_test("diff --git a/README.md b/README.md")


@pytest.mark.integration
def test_int_pr_comment(mock_github) -> None:
    """Integration Test for GitHub API comment call."""
    post_pr_comment_test()


@pytest.mark.integration
def test_int_pr_update(mock_github, mock_github_comment) -> None:
    """Integration Test for updating GitHub API comment call."""
    post_pr_comment_test()


def test_pr_comment(mock_openai, mock_github) -> None:
    """Unit Test for GitHub API comment call."""
    post_pr_comment_test()


def test_pr_update(mock_openai, mock_github, mock_github_comment) -> None:
    """Unit Test for updating GitHub API comment call."""
    post_pr_comment_test()
