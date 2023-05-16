"""Azure DevOps Package Wrappers to Simplify Usage."""
from __future__ import annotations

import abc
import itertools
import json
import logging
import os
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from azure.devops.connection import Connection
from azure.devops.exceptions import AzureDevOpsServiceError
from azure.devops.v7_1.git.git_client import GitClient
from azure.devops.v7_1.git.models import (
    Comment,
    GitBaseVersionDescriptor,
    GitPullRequest,
    GitTargetVersionDescriptor,
    GitVersionDescriptor,
)
from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup
from msrest.authentication import BasicAuthentication


from gpt_review._ask import _ask
from gpt_review._command import GPTCommandGroup
from gpt_review._review import _summarize_files
from gpt_review.repositories._repository import _RepositoryClient

MIN_CONTEXT_LINES = 5
SURROUNDING_CONTEXT = 5


class _DevOpsClient(_RepositoryClient, abc.ABC):
    """Azure DevOps API Client Wrapper."""

    def __init__(self, pat, org, project, repository_id) -> None:
        """
        Initialize the client.

        Args:
            pat (str): The Azure DevOps personal access token.
            org (str): The Azure DevOps organization.
            project (str): The Azure DevOps project.
            repository_id (str): The Azure DevOps repository ID.
        """
        self.pat = pat
        self.org = org
        self.project = project
        self.repository_id = repository_id

        personal_access_token = pat
        organization_url = f"https://dev.azure.com/{org}"

        # Create a connection to the org
        credentials = BasicAuthentication("", personal_access_token)
        connection = Connection(base_url=organization_url, creds=credentials)

        # Get a client (the "core" client provides access to projects, teams, etc)
        self.connection = connection
        self.client: GitClient = connection.clients_v7_1.get_git_client()
        self.project = project
        self.repository_id = repository_id

    def create_comment(self, pull_request_id: int, comment_id: int, text) -> Comment:
        """
        Create a comment on a pull request.

        Args:
            token (str): The Azure DevOps token.
            org (str): The Azure DevOps organization.
            project (str): The Azure DevOps project.
            repository_id (str): The Azure DevOps repository ID.
            pull_request_id (int): The Azure DevOps pull request ID.
            comment_id (int): The Azure DevOps comment ID.
            text (str): The text of the comment.

        Returns:
            Comment: The response from the API.
        """
        new_comment = Comment(content=text)
        return self.client.create_comment(
            new_comment, self.repository_id, pull_request_id, comment_id, project=self.project
        )

    def update_pr(self, pull_request_id, title=None, description=None) -> GitPullRequest:
        """
        Update a pull request.

        Args:
            pull_request_id (str): The Azure DevOps pull request ID.
            title (str): The title of the pull request.
            description (str): The description of the pull request.

        Returns:
            GitPullRequest: The response from the API.
        """
        return self.client.update_pull_request(
            git_pull_request_to_update=GitPullRequest(title=title, description=description),
            repository_id=self.repository_id,
            project=self.project,
            pull_request_id=pull_request_id,
        )

    def read_all_text(
        self,
        path: str,
        commit_id: str = None,
        **kwargs,
    ) -> str:
        """
        Read all text from a file.

        Args:
            path (str): The path to the file.
            commit_id (str): The commit ID.
            **kwargs: Any additional keyword arguments.

        Returns:
            str: The text of the file.
        """
        byte_iterator = self.client.get_item_content(
            repository_id=self.repository_id,
            path=path,
            project=self.project,
            version_descriptor=GitVersionDescriptor(commit_id, version_type="commit") if commit_id else None,
            **kwargs,
        )
        return "".join(byte.decode("utf-8") for byte in byte_iterator)

    @staticmethod
    def process_comment_payload(payload: str) -> str:
        """
        Extract question from Service Bus payload.

        Args:
            payload (str): The Service Bus payload.

        Returns:
            str: The question from the Azure DevOps Comment.
        """
        payload = json.loads(payload)
        return payload["resource"]["comment"]["content"]

    def get_patch(self, pull_request_event, pull_request_id, comment_id) -> List[str]:
        """
        Get the diff of a pull request.

        Args:
            pull_request_event (dict): The pull request event.
            pull_request_id (str): The Azure DevOps pull request ID.
            comment_id (str): The Azure DevOps comment ID.

        Returns:
            List[str]: The diff of the pull request.
        """
        thread = self.client.get_pull_request_thread(
            repository_id=self.repository_id,
            pull_request_id=pull_request_id,
            thread_id=comment_id,
            project=self.project,
        )
        thread_context = thread.thread_context

        pull_request = pull_request_event["pullRequest"]
        if not pull_request:
            raise ValueError("pull_request_event.pullRequest is required")

        original_content = self.read_all_text(path=thread_context.file_path, check_if_exists=True)
        changed_content = self.read_all_text(
            path=thread_context.file_path,
            commit_id=pull_request["lastMergeSourceCommit"]["commitId"],
            check_if_exists=True,
        )

        left_selection, right_selection = self._calculate_selection(thread_context, original_content, changed_content)

        return self._create_patch(
            "\n".join(left_selection) or [], "\n".join(right_selection) or [], thread_context.file_path
        )

    def _calculate_selection(self, thread_context, original_content, changed_content) -> Tuple[List[str], List[str]]:
        """
        Calculate the selection for a given thread context.

        Args:
            thread_context (CommentThreadContext): The thread context.
            original_content (str): The original content.
            changed_content (str): The changed content.

        Returns:
            Tuple[List[str], List[str]]: The left and right selections.
        """
        left_selection = []
        right_selection = []
        if original_content and thread_context.left_file_start and thread_context.left_file_end:
            left_selection = self._get_selection(
                original_content, thread_context.left_file_start.line, thread_context.left_file_end.line
            )

            if not changed_content or not thread_context.right_file_start or not thread_context.right_file_end:
                raise ValueError("Both left and right selection cannot be None")

            right_selection = self._get_selection(
                changed_content, thread_context.right_file_start.line, thread_context.right_file_end.line
            )

        if changed_content and thread_context.right_file_start and thread_context.right_file_end:
            right_selection = self._get_selection(
                changed_content, thread_context.right_file_start.line, thread_context.right_file_end.line
            )

        return left_selection, right_selection

    def get_patches(self, pull_request_event, condensed=False) -> Iterable[List[str]]:
        """
        Get the patches for a given pull request event.

        Args:
            pull_request_event (Any): The pull request event to retrieve patches for.
            condensed (bool, optional): If True, returns a condensed version of the patch. Defaults to False.

        Returns:
            Iterable[List[str]]: An iterable of lists containing the patches for the pull request event.
        """
        pull_request_id = pull_request_event["pullRequest"]["pullRequestId"]
        if not pull_request_id:
            raise ValueError("pull_request_event.pullRequest is required")

        git_changes = self.get_changed_blobs(pull_request_event["pullRequest"])
        return [
            self._get_change(
                git_change,
                pull_request_event["pullRequest"]["lastMergeSourceCommit"]["commitId"],
                condensed,
            )
            for git_change in git_changes
        ]

    def get_changed_blobs(self, pull_request: GitPullRequest):
        """
        Get the changed blobs in a pull request.

        Args:
            pull_request (GitPullRequest): The pull request.

        Returns:
            List[Dict[str, str]]: The changed blobs.
        """
        changed_paths = []
        commit_diff_within_pr = None

        skip = 0
        while True:
            commit_diff_within_pr = self.client.get_commit_diffs(
                repository_id=self.repository_id,
                project=self.project,
                diff_common_commit=False,
                base_version_descriptor=GitBaseVersionDescriptor(
                    base_version=pull_request["lastMergeSourceCommit"]["commitId"], base_version_type="commit"
                ),
                target_version_descriptor=GitTargetVersionDescriptor(
                    target_version=pull_request["lastMergeTargetCommit"]["commitId"], target_version_type="commit"
                ),
            )
            changed_paths.extend(
                [change for change in commit_diff_within_pr.changes if "isFolder" not in change["item"]]
            )
            skip += len(commit_diff_within_pr.changes)
            if commit_diff_within_pr.all_changes_included:
                break

        return changed_paths

    def _get_selection(self, file_contents: str, line_start: int, line_end: int) -> List[str]:
        lines = file_contents.splitlines()

        if line_end - line_start < MIN_CONTEXT_LINES:
            return lines

        if line_start < 1 or line_start > len(lines) or line_end < 1 or line_end > len(lines):
            raise ValueError(
                f"Selection region lineStart = {line_start}, lineEnd = {line_end}, lines length = {len(lines)}"
            )

        if line_start == line_end:
            return [lines[line_start - 1]]

        return lines[line_start - 1 : line_end]

    def _get_change(self, git_change, source_commit_head, condensed=False) -> List[str]:
        return "\n".join(self._get_git_change(git_change["item"]["path"], source_commit_head, condensed))

    def _get_git_change(self, file_path, source_commit_head, condensed=False) -> List[str]:
        try:
            original_content = self.read_all_text(file_path, check_if_exists=True)
        except AzureDevOpsServiceError:
            # File Not Found
            original_content = ""
        changed_content = self.read_all_text(file_path, commit_id=source_commit_head, check_if_exists=True)
        return self._create_patch(original_content, changed_content, file_path, condensed)

    def _create_patch(
        self, original_content: Optional[str], changed_content: Optional[str], file_path: str, condensed=False
    ) -> List[str]:
        """
        Create a patch for a given file.

        Args:
            original_content (Optional[str]): The original content.
            changed_content (Optional[str]): The changed content.
            file_path (str): The file path.
            condensed (bool, optional): If True, returns a condensed version of the patch. Defaults to False.

        Returns:
            List[str]: The patch.
        """
        left = original_content.splitlines() if original_content else []
        right = changed_content.splitlines() if changed_content else []
        return self._create_patch_list(left, right, file_path, condensed)

    def _create_patch_list(self, left: List[str], right: List[str], file_path: str, condensed=False) -> List[str]:
        """
        Create a patch list for a given file.

        Args:
            left (List[str]): The left side of the patch.
            right (List[str]): The right side of the patch.
            file_path (str): The file path.
            condensed (bool, optional): If True, returns a condensed version of the patch. Defaults to False.

        Returns:
            List[str]: The patch list.
        """
        needed_changes = self._calculate_minimum_change_needed(left, right)
        line, row = 1, 1
        patch = []

        while line < len(left) and row < len(right):
            if needed_changes[line][row] == needed_changes[line - 1][row - 1]:
                patch.append(left[line - 1])
                line += 1
                row += 1
            elif needed_changes[line - 1][row] < needed_changes[line][row - 1]:
                patch.append(f"- {left[line - 1]}")
                line += 1
            else:
                patch.append(f"+ {right[row - 1]}")
                row += 1

        while line <= len(left):
            patch.append(f"- {left[line - 1]}")
            line += 1

        while row <= len(right):
            patch.append(f"+ {right[row - 1]}")
            row += 1

        if condensed:
            patch = self._get_condensed_patch(patch)

        patch.insert(0, file_path)
        return patch

    def _get_condensed_patch(self, patch: List[str]) -> List[str]:
        """
        Get a condensed version of the patch.

        Args:
            patch (List[str]): The patch.

        Returns:
            List[str]: The condensed patch.
        """
        buffer = []
        result = []
        trailing_context = 0

        for line in patch:
            if line.startswith("+") or line.startswith("-"):
                result.extend(buffer[-SURROUNDING_CONTEXT:])
                buffer.clear()
                result.append(line)
                trailing_context = SURROUNDING_CONTEXT
            elif trailing_context > 0:
                result.append(line)
                trailing_context -= 1
            else:
                buffer.append(line)

        return result

    def _calculate_minimum_change_needed(self, left: List[str], right: List[str]) -> List[List[int]]:
        """
        Calculate the minimum change needed to transform the left side to the right side.

        Args:
            left (List[str]): The left side of the patch.
            right (List[str]): The right side of the patch.

        Returns:
            List[List[int]]: The minimum change needed.
        """
        changes = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]

        for i, j in itertools.product(range(len(left) + 1), range(len(right) + 1)):
            if i == 0 or j == 0:
                changes[i][j] = 0
            elif left[i - 1] == right[j - 1]:
                changes[i][j] = changes[i - 1][j - 1]
            else:
                changes[i][j] = 1 + min(changes[i - 1][j], changes[i][j - 1], changes[i - 1][j - 1])

        return changes


class DevOpsClient(_DevOpsClient):
    """Azure DevOps client Wrapper for working with."""

    @staticmethod
    def post_pr_summary(diff, link=None, access_token=None) -> Dict[str, str]:
        """
        Get a review of a PR.

        Requires the following environment variables:
            - LINK: The link to the PR.
                Example: https://<org>.visualstudio.com/<project>/_git/<repo>/pullrequest/<pr_id>
                    or   https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<pr_id>
            - ADO_TOKEN: The GitHub access token.

        Args:
            diff (str): The patch of the PR.

        Returns:
            Dict[str, str]: The review.
        """
        link = os.getenv("LINK", link)
        access_token = os.getenv("ADO_TOKEN", access_token)

        if link and access_token:
            review = _summarize_files(diff)

            parsed_url = urlparse(link)

            if "dev.azure.com" in parsed_url.netloc:
                org = link.split("/")[3]
                project = link.split("/")[4]
                repo = link.split("/")[6]
                pr_id = link.split("/")[8]
            else:
                org = link.split("/")[2].split(".")[0]
                project = link.split("/")[3]
                repo = link.split("/")[5]
                pr_id = link.split("/")[7]

            DevOpsClient(pat=access_token, org=org, project=project, repository_id=repo).update_pr(
                pull_request_id=pr_id,
                description=review,
            )
            return {"response": "PR posted"}

        logging.warning("No PR to post too")
        return {"response": "No PR to post too"}

    @staticmethod
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


class DevOpsFunction(DevOpsClient):
    """Azure Function for process Service Messages from Azure DevOps."""

    def handle(self, msg) -> None:
        """
        The main function for the Azure Function.

        Args:
            msg (func.QueueMessage): The Service Bus message.
        """
        body = msg.get_body().decode("utf-8")
        logging.info("Python ServiceBus queue trigger processed message: %s", body)
        if "copilot:summary" in body:
            self._process_summary(body)
        elif "copilot:" in body:
            self._process_comment(body)

    def _process_comment(self, body) -> None:
        """
        Process a comment from Copilot.

        Args:
            body (str): The Service Bus payload.
        """
        logging.info("Copilot Comment Alert Triggered")
        payload = json.loads(body)

        pr_id = self._get_pr_id(payload)

        comment_id = self._get_comment_id(payload)

        try:
            diff = self.get_patch(pull_request_event=payload["resource"], pull_request_id=pr_id, comment_id=comment_id)
        except Exception:
            diff = self.get_patches(pull_request_event=payload["resource"])

        logging.info("Copilot diff: %s", diff)
        diff = "\n".join(diff)

        question = f"""
    {diff}

    {_DevOpsClient.process_comment_payload(body)}
    """

        response = _ask(
            question=question,
            max_tokens=500,
        )
        self.create_comment(pull_request_id=pr_id, comment_id=comment_id, text=response["response"])

    def _get_comment_id(self, payload) -> int:
        """
        Get the comment ID from the payload.

        Args:
            payload (dict): The payload from the Service Bus.

        Returns:
            int: The comment ID.
        """
        comment_id = payload["resource"]["comment"]["_links"]["threads"]["href"].split("/")[-1]
        logging.info("Copilot Commet ID: %s", comment_id)
        return comment_id

    def _process_summary(self, body) -> None:
        """
        Process a summary from Copilot.

        Args:
            body (str): The Service Bus payload.
        """
        logging.info("Copilot Summary Alert Triggered")
        payload = json.loads(body)

        pr_id = self._get_pr_id(payload)

        link = self._get_link(pr_id)

        if "comment" in payload["resource"]:
            self._post_summary(payload, pr_id, link)
        else:
            logging.info("Copilot Update from Updated PR")

    def _get_link(self, pr_id) -> str:
        link = f"https://{self.org}.visualstudio.com/{self.project}/_git/{self.repository_id}/pullrequest/{pr_id}"
        logging.info("Copilot Link: %s", link)
        return link

    def _get_pr_id(self, payload) -> int:
        """
        Get the pull request ID from the Service Bus payload.

        Args:
            payload (dict): The Service Bus payload.

        Returns:
            int: The pull request ID.
        """
        if "pullRequestId" in payload:
            pr_id = payload["resource"]["pullRequestId"]
        else:
            pr_id = payload["resource"]["pullRequest"]["pullRequestId"]
        logging.info("Copilot PR ID: %s", pr_id)
        return pr_id

    def _post_summary(self, payload, pr_id, link) -> None:
        """
        Process a summary from Copilot.

        Args:
            payload (dict): The Service Bus payload.
            pr_id (str): The Azure DevOps pull request ID.
            link (str): The link to the PR.
        """
        comment_id = payload["resource"]["comment"]["_links"]["threads"]["href"].split("/")[-1]
        logging.info("Copilot Commet ID: %s", comment_id)

        os.putenv("RISK_SUMMARY", "false")
        os.putenv("FILE_SUMMARY_FULL", "false")
        os.putenv("TEST_SUMMARY", "false")
        os.putenv("BUG_SUMMARY", "false")
        os.putenv("SUMMARY_SUGGEST", "false")

        diff = self.get_patch(pull_request_event=payload["resource"], pull_request_id=pr_id, comment_id=comment_id)
        diff = "\n".join(diff)
        logging.info("Copilot diff: %s", diff)

        self.post_pr_summary(diff, link=link)


def _review(diff: str = ".diff", link=None, access_token=None) -> Dict[str, str]:
    """Review Azure DevOps PR with Open AI, and post response as a comment.

    Args:
        link (str): The link to the PR.
        access_token (str): The Azure DevOps access token.

    Returns:
        Dict[str, str]: The response.
    """
    # diff = _DevOpsClient.get_pr_diff(repository, pull_request, access_token)
    with open(diff, "r", encoding="utf8") as file:
        diff_contents = file.read()

    DevOpsClient.post_pr_summary(diff_contents, link, access_token)
    return {"response": "Review posted as a comment."}


def _comment(question: str, comment_id: int, diff: str = ".diff", link=None, access_token=None) -> Dict[str, str]:
    """Review Azure DevOps PR with Open AI, and post response as a comment.

    Args:
        question (str): The question to ask.
        comment_id (int): The comment ID.
        diff(str): The diff file.
        link (str): The link to the PR.
        access_token (str): The Azure DevOps access token.

    Returns:
        Dict[str, str]: The response.
    """
    # diff = _DevOpsClient.get_pr_diff(repository, pull_request, access_token)

    if os.path.exists(diff):
        with open(diff, "r", encoding="utf8") as file:
            diff_contents = file.read()
            question = f"{diff_contents}\n{question}"

    link = os.getenv("LINK", link)
    access_token = os.getenv("ADO_TOKEN", access_token)

    if link and access_token:
        response = _ask(
            question=question,
        )
        parsed_url = urlparse(link)

        if "dev.azure.com" in parsed_url.netloc:
            org = link.split("/")[3]
            project = link.split("/")[4]
            repo = link.split("/")[6]
            pr_id = link.split("/")[8]
        else:
            org = link.split("/")[2].split(".")[0]
            project = link.split("/")[3]
            repo = link.split("/")[5]
            pr_id = link.split("/")[7]

        DevOpsClient(pat=access_token, org=org, project=project, repository_id=repo).create_comment(
            pull_request_id=pr_id, comment_id=comment_id, text=response["response"]
        )
        return {"response": "Review posted as a comment.", "text": response["response"]}
    raise ValueError("LINK and ADO_TOKEN must be set.")


class DevOpsCommandGroup(GPTCommandGroup):
    """Ask Command Group."""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        with CommandGroup(loader, "ado", "gpt_review.repositories.devops#{}", is_preview=True) as group:
            group.command("review", "_review", is_preview=True)
            group.command("comment", "_comment", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader) -> None:
        """Add patch_repo, patch_pr, and access_token arguments."""
        with ArgumentsContext(loader, "ado") as args:
            args.argument(
                "diff",
                type=str,
                help="Git diff to review.",
                default=".diff",
            )
            args.argument(
                "access_token",
                type=str,
                help="The Azure DevOps access token, or set ADO_TOKEN",
                default=None,
            )
            args.argument(
                "link",
                type=str,
                help="The link to the PR.",
                default=None,
            )

        with ArgumentsContext(loader, "ado comment") as args:
            args.positional("question", type=str, nargs="+", help="Provide a question to ask GPT.")
            args.argument(
                "comment_id",
                type=int,
                help="The comment ID of Azure DevOps Pull Request Comment.",
                default=None,
            )
