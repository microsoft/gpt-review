import pytest

from gpt_review._github import _GitHubClient


def get_pr_diff_test(starts_with, patch_repo=None, patch_pr=None) -> None:
    """Test the GitHub API call."""
    diff = _GitHubClient.get_pr_diff(patch_repo=patch_repo, patch_pr=patch_pr)
    assert diff.startswith(starts_with)


def post_pr_comment_test() -> None:
    """Test the GitHub API call."""
    response = _GitHubClient._post_pr_comment(
        "test",
        git_commit_hash="a9da0c1e65f1102bc2ae16abed7b6a66400a5bde",
        link="https://github.com/microsoft/gpt-review/pull/1",
    )
    assert response


@pytest.mark.skip(reason="Creds for action missing on build server")
@pytest.mark.integration
def test_int_pr_diff() -> None:
    """Integration Test for GitHub API diff call."""
    get_pr_diff_test("diff --git a/.devcontainer/Dockerfile b/.devcontainer/Dockerfile", "microsoft/gpt-review", 1)


def test_pr_diff(mock_github) -> None:
    """Unit Test for GitHub API diff call."""
    get_pr_diff_test("diff --git a/README.md b/README.md")


@pytest.mark.skip(reason="Creds for action missing on build server")
@pytest.mark.integration
def test_int_pr_comment() -> None:
    """Integration Test for GitHub API comment call."""
    post_pr_comment_test()


def test_pr_comment(mock_github) -> None:
    """Unit Test for GitHub API comment call."""
    post_pr_comment_test()
