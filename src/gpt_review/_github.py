"""GitHub API helpers."""
import logging
import json
import os
from typing import Dict

import requests
from knack.arguments import ArgumentsContext
from knack import CLICommandsLoader
from knack.commands import CommandGroup

from gpt_review._command import GPTCommandGroup
from gpt_review._review import summarize_files


def get_pr_diff(patch_repo=None, patch_pr=None, access_token=None) -> str:
    """
    Replicate the logic from this command to get the PR diff:

    PATCH_OUTPUT=$(curl --silent --request GET \
        --url https://api.github.com/repos/$PATCH_REPO/pulls/$PATCH_PR \
        --header "Accept: application/vnd.github.diff" \
        --header "Authorization: Bearer $GITHUB_TOKEN")
    """
    patch_repo = patch_repo or os.getenv("PATCH_REPO")
    patch_pr = patch_pr or os.getenv("PATCH_PR")
    access_token = access_token or os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "authorization": f"Bearer {access_token}",
    }

    response = requests.get(f"https://api.github.com/repos/{patch_repo}/pulls/{patch_pr}", headers=headers, timeout=10)
    return response.text


def _post_pr_comment(review, git_commit_hash=None, link=None, access_token=None) -> requests.Response:
    """
    Replicate the logic from this command to post a PR comment:

    curl --request POST \
        --url https://api.github.com/repos/$OWNER/$REPO/pulls/$PULL_NUMBER/reviews \
        --header 'Accept: application/vnd.github.v3+json' \

    """
    git_commit_hash = git_commit_hash or os.getenv("GIT_COMMIT_HASH")
    data = {"body": review, "commit_id": git_commit_hash, "event": "COMMENT"}
    data = json.dumps(data)

    pr_link = link or os.getenv("LINK")
    if not isinstance(pr_link, str):
        raise ValueError("PR link not found, set the LINK environment variable.")
    owner = pr_link.split("/")[-4]
    repo = pr_link.split("/")[-3]
    pr_number = pr_link.split("/")[-1]

    access_token = access_token or os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "authorization": f"Bearer {access_token}",
    }
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews", headers=headers, timeout=10
    )
    comments = response.json()

    for comment in comments:
        if (
            "user" in comment
            and comment["user"]["login"] == "github-actions[bot]"
            and "body" in comment
            and "Summary by GPT-4" in comment["body"]
        ):
            review_id = comment["id"]
            data = {"body": review}
            data = json.dumps(data)

            response = requests.put(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}",
                headers=headers,
                data=data,
                timeout=10,
            )
            break
    else:
        # https://api.github.com/repos/OWNER/REPO/pulls/PULL_NUMBER/reviews
        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            headers=headers,
            data=data,
            timeout=10,
        )
    logging.info(response.json())
    return response


def get_review(pr_patch) -> None:
    """Get a review of a PR.
    Args:
        pr_patch (str): The patch of the PR.
    Returns:
        str: The review of the PR.
    """

    review = summarize_files(pr_patch)
    print(review)

    if os.getenv("LINK"):
        _post_pr_comment(review)
    else:
        logging.warning("No PR to post too")


def _github_review(repository=None, pull_request=None, access_token=None) -> Dict[str, str]:
    """Review GitHub PR with Open AI, and post response as a comment."""
    diff = get_pr_diff(repository, pull_request, access_token)
    get_review(diff)
    return {"response": "Review posted as a comment."}


class GitHubCommandGroup(GPTCommandGroup):
    """Ask Command Group."""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        with CommandGroup(loader, "github", "gpt_review._github#{}") as group:
            group.command("review", "_github_review", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader) -> None:
        """Add patch_repo, patch_pr, and access_token arguments."""
        with ArgumentsContext(loader, "github") as args:
            args.argument(
                "access_token",
                type=str,
                help="The GitHub access token. Set or use GITHUB_TOKEN environment variable.",
                default=None,
            )
            args.argument(
                "pull_request",
                type=str,
                help="The PR number. Set or use PATCH_PR environment variable.",
                default=None,
                options_list=("--pull-request", "-pr"),
            )
            args.argument(
                "repository",
                type=str,
                help="The repo of the PR. Set or use PATCH_REPO environment variable.",
                default=None,
                options_list=("--repository", "-r"),
            )
