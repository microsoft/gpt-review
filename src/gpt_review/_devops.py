"""Azure DevOps API client."""
import base64
import os
import logging
from typing import Dict

from httpx import RequestError
import requests

from knack.arguments import ArgumentsContext
from knack import CLICommandsLoader
from knack.commands import CommandGroup

from gpt_review._command import GPTCommandGroup
from gpt_review._repository import _RepositoryClient
from gpt_review._review import _summarize_files


class _DevOpsClient(_RepositoryClient):
    """Azure DevOps Client"""

    @staticmethod
    def get_pr_diff(repository=None, pull_request=None, access_token=None, organization=None, project=None) -> str:
        """
        Get the diff of a PR From Azure DevOps.

        Args:
            repository (str): The repo.
            pull_request (str): The PR.
            access_token (str): The GitHub access token.

        Returns:
            str: The diff of the PR.
        """
        organization = organization or os.getenv("AZURE_DEVOPS_ORGANIZATION")
        project = project or os.getenv("AZURE_DEVOPS_PROJECT")
        repository_id = repository or os.getenv("AZURE_DEVOPS_REPOSITORY")
        pull_request_id = pull_request or os.getenv("AZURE_DEVOPS_PULL_REQUEST")
        personal_access_token = access_token or os.getenv("AZURE_DEVOPS_TOKEN")

        credentials = ("", personal_access_token)
        credentials_base64 = base64.b64encode(credentials[1].encode())
        headers = {"Authorization": f"Basic {credentials_base64.decode()}", "Content-Type": "application/json"}

        root = f"https://dev.azure.com/{organization}/{project}"
        url = f"{root}/_apis/git/repositories/{repository_id}/pullRequests/{pull_request_id}/diffs?api-version=6.0"

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        raise RequestError(f"Error {response.status_code}: {response.text}")

    @staticmethod
    def create_pr_summary(pr_patch, post: bool = True) -> str:
        """
        Create a summary to a PR.

        Args:
            pr_patch (str): The patch of the PR.

        Returns:
            str: The review of the PR.
        """
        review = _summarize_files(pr_patch)
        logging.debug(review)
        if post:
            print(f"##vso[task.addattachment type=Distributedtask.Core.Summary;name=SUMMARY;]{review}")
        return review


def _devops_review(
    repository=None, pull_request=None, access_token=None, organization=None, project=None, post: bool = False
) -> Dict[str, str]:
    """
    Create a summary to a PR.

    Args:
        repository (str): The repo.
        pull_request (str): The PR.
        access_token (str): The GitHub access token.

    Returns:
        str: The review of the PR.
    """
    pr_patch = _DevOpsClient.get_pr_diff(
        repository=repository,
        pull_request=pull_request,
        access_token=access_token,
        organization=organization,
        project=project,
    )
    review = _DevOpsClient.create_pr_summary(pr_patch, post=post)

    return {"review": review}


class DevOpsCommandGroup(GPTCommandGroup):
    """Ask Command Group."""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        with CommandGroup(loader, "devops", "gpt_review._devops#{}") as group:
            group.command("review", "_devops_review", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader) -> None:
        """Add patch_repo, patch_pr, and access_token arguments."""
        with ArgumentsContext(loader, "devops review") as args:
            args.argument(
                "access_token",
                type=str,
                help="The Azure DevOps access token. Set or use AZURE_DEVOPS_TOKEN environment variable.",
                default=None,
            )
            args.argument(
                "pull_request",
                type=str,
                help="The PR. Set or use AZURE_DEVOPS_PULL_REQUEST environment variable.",
                default=None,
                options_list=("--pull-request", "-pr"),
            )
            args.argument(
                "repository",
                type=str,
                help="The repo. Set or use AZURE_DEVOPS_REPOSITORY environment variable.",
                default=None,
                options_list=("--repository", "-r"),
            )
            args.argument(
                "organization",
                type=str,
                help="The organization of the PR. Set or use AZURE_DEVOPS_ORGANIZATION environment variable.",
                default=None,
                options_list=("--organization", "-org"),
            )
            args.argument(
                "project",
                type=str,
                help="The project of the PR. Set or use AZURE_DEVOPS_PROJECT environment variable.",
                default=None,
                options_list=("--project", "-p"),
            )
            args.argument(
                "post",
                type=str,
                help="The project of the PR. Set or use AZURE_DEVOPS_PROJECT environment variable.",
                default=False,
                action="store_true",
            )
