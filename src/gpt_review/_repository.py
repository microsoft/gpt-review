"""Abstract class for a repository client."""
from abc import abstractmethod
import requests


class RepositoryClient:
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
    def _post_pr_comment(review, git_commit_hash=None, link=None, access_token=None) -> requests.Response:
        """
        Post a comment to a PR.

        Args:
            review (str): The review.
            git_commit_hash (str): The git commit hash.
            link (str): The link to the PR.
            access_token (str): The GitHub access token.

        Returns:
            requests.Response: The response.
        """

    @staticmethod
    @abstractmethod
    def get_review(pr_patch) -> None:
        """Get a review of a PR.
        Args:
            pr_patch (str): The patch of the PR.
        Returns:
            str: The review of the PR.
        """
