"""Abstract class for a repository client."""
from abc import abstractmethod


class _RepositoryClient:
    """Abstract class for a repository client."""

    @staticmethod
    @abstractmethod
    def get_pr_diff(repository=None, pull_request=None, access_token=None) -> str:
        """
        Get the diff of a PR.

        Args:
            repository (str): The repo.
            pull_request (str): The PR.
            access_token (str): The GitHub access token.

        Returns:
            str: The diff of the PR.
        """

    @staticmethod
    @abstractmethod
    def create_pr_summary(pr_patch: str, post: bool = True) -> str:
        """
        Post a summary to a PR.

        Args:
            pr_patch (str): The patch of the PR.
            post (bool, optional): Whether to post the summary to the PR. Defaults to True.

        Returns:
            str: The review of the PR.
        """
