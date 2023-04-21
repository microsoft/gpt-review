"""Source Control Platform Interface."""
import os
import logging
import json

from abc import abstractmethod

import requests


class SourceControl:
    """Basic Interface for Source Control Platforms."""

    @abstractmethod
    def get_diff(self):
        """
        Get the diff of a PR

        Returns:
            str: The diff of the PR.
        """

    @abstractmethod
    def post_pr_comment(self, review):
        """
        Post a comment on a PR.

        Args:
            review (str): The text of the comment.
        """


class Local(SourceControl):
    def get_diff(self):
        return os.getenv("DIFF")

    def post_pr_comment(self, review):
        raise NotImplementedError


class GitHub(SourceControl):
    ROOT = "https://api.github.com/repos/"

    def get_diff(self):
        patch_repo = os.getenv("PATCH_REPO")
        patch_pr = os.getenv("PATCH_PR")
        access_token = os.getenv("GITHUB_TOKEN")
        return self._get_diff(patch_repo, patch_pr, access_token)

    def _get_diff(self, patch_repo, patch_pr, access_token):
        """
        Get the diff of a PR

        Args:
            patch_repo (str): The repo of the PR.
            patch_pr (str): The PR number.
            access_token (str): The access token to use.

        Returns:
            str: The diff of the PR.
        """

        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "authorization": f"Bearer {access_token}",
        }
        url = f"{self.ROOT}{patch_repo}/pulls/{patch_pr}"
        response = requests.get(url, headers=headers, timeout=10)
        return response.text

    def post_pr_comment(self, review):
        git_commit_hash = os.getenv("GIT_COMMIT_HASH")
        pr_link = os.getenv("LINK")
        return self._post_pr_comment(review, git_commit_hash, pr_link)

    def _post_pr_comment(self, review, git_commit_hash, pr_link):
        data = {"body": review, "commit_id": git_commit_hash, "event": "COMMENT"}
        data = json.dumps(data)

        if pr_link:
            owner = pr_link.split("/")[-4]
            repo = pr_link.split("/")[-3]
            pr_number = pr_link.split("/")[-1]

            data = {"body": review}
            data = json.dumps(data)

            access_token = os.getenv("GITHUB_TOKEN")
            headers = {
                "Accept": "application/vnd.github+json",
                "authorization": f"Bearer {access_token}",
            }
            response = requests.get(f"{self.ROOT}{owner}/{repo}/pulls/{pr_number}/reviews", headers=headers, timeout=10)
            comments = response.json()

            for comment in comments:
                if (
                    "user" in comment
                    and comment["user"]["login"] == "github-actions[bot]"
                    and "body" in comment
                    and "Summary by GPT-4" in comment["body"]
                ):
                    review_id = comment["id"]

                    response = requests.put(
                        f"{self.ROOT}{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}",
                        headers=headers,
                        data=data,
                        timeout=10,
                    )
                    logging.info(response.json())
                    break
            else:
                # {ROOT}OWNER/REPO/pulls/PULL_NUMBER/reviews
                response = requests.post(
                    f"{self.ROOT}{owner}/{repo}/pulls/{pr_number}/reviews",
                    headers=headers,
                    data=data,
                    timeout=10,
                )
                logging.info(response.json())


class AzureDevOps(SourceControl):
    def get_diff(self):
        raise NotImplementedError

    def post_pr_comment(self):
        raise NotImplementedError
