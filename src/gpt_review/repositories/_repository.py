"""Abstract class for a repository client."""
from abc import abstractmethod
from typing import Dict


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
    def post_pr_summary(diff) -> None:
        """
        Post a summary to a PR.

        Args:
            diff (str): The diff of the PR.

        Returns:
            str: The review of the PR.
        """

    @staticmethod
    @abstractmethod
    def _review(repository=None, pull_request=None, access_token=None) -> Dict[str, str]:
        """Review PR with Open AI, and post response as a comment.

        Args:
            repository (str): The repo of the PR.
            pull_request (str): The PR number.
            access_token (str): The GitHub access token.

        Returns:
            Dict[str, str]: The response.
        """

    @staticmethod
    @abstractmethod
    def _comment(question: str, comment_id: int, diff: str = ".diff", link=None, access_token=None) -> Dict[str, str]:
        """Review PR with Open AI, and post response as a comment.

        Args:
            question (str): The question to ask.
            comment_id (int): The comment ID.
            diff(str): The diff file.
            link (str): The link to the PR.
            access_token (str): The Azure DevOps access token.

        Returns:
            Dict[str, str]: The response.
        """
