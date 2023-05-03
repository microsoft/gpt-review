"""Abstract class for a repository client."""
from abc import abstractmethod


class _RepositoryClient:
    """Abstract class for a repository client."""

    @staticmethod
    @abstractmethod
    def get_pr_diff(patch_repo=None, patch_pr=None, access_token=None) -> str:
        """
        Get the diff of a PR.

        Args:
            patch_repo (str): The repo.
            patch_pr (str): The PR.
            access_token (str): The GitHub access token.

        Returns:
            str: The diff of the PR.
        """

    @staticmethod
    @abstractmethod
    def post_pr_summary(pr_patch) -> None:
        """
        Post a summary to a PR.

        Args:
            pr_patch (str): The patch of the PR.

        Returns:
            str: The review of the PR.
        """
