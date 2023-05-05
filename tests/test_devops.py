import pytest
from gpt_review._devops import _DevOpsClient


def get_pr_diff_test(starts_with) -> None:
    """Test the Azure DevOps API call."""
    diff = _DevOpsClient.get_pr_diff()
    assert diff.startswith(starts_with)


def create_pr_summary_test(pr_patch) -> None:
    """Test the Azure DevOps PR summary creation."""
    review = _DevOpsClient.create_pr_summary(pr_patch)
    assert review


@pytest.mark.integration
def test_int_pr_diff(devops_creds) -> None:
    """Integration Test for Azure DevOps API diff call."""
    get_pr_diff_test("diff --git a/.devcontainer/Dockerfile b/.devcontainer/Dockerfile")


def test_pr_diff(mock_devops) -> None:
    """Unit Test for Azure DevOps API diff call."""
    get_pr_diff_test("diff --git a/README.md b/README.md")


@pytest.mark.integration
def test_int_create_pr_summary(devops_creds) -> None:
    """Integration Test for Azure DevOps PR summary creation."""
    pr_patch = "your-pr-patch"
    create_pr_summary_test(pr_patch)


def test_create_pr_summary(mock_devops) -> None:
    """Unit Test for Azure DevOps PR summary creation."""
    pr_patch = "your-pr-patch"
    create_pr_summary_test(pr_patch)
