"""Azure DevOps Package Wrappers to Simplify Usage."""
import abc
import itertools
import json
import logging
import os
import urllib.parse
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup
from msrest.authentication import BasicAuthentication

from azure.devops.connection import Connection
from azure.devops.exceptions import AzureDevOpsServiceError
from azure.devops.v7_1.git.git_client import GitClient
from azure.devops.v7_1.git.models import (
    Comment,
    GitBaseVersionDescriptor,
    GitPullRequest,
    GitCommitRef,
    GitTargetVersionDescriptor,
    GitVersionDescriptor,
    GitPullRequestCommentThread,
)

from gpt_review._ask import _ask
from gpt_review._command import GPTCommandGroup
from gpt_review._review import _summarize_files
from gpt_review.prompts._prompt import load_ask_yaml
from gpt_review.repositories._repository import _RepositoryClient
import gpt_review.repositories.devops_constants as C


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
        self.connection = Connection(base_url=organization_url, creds=credentials)

        # Get a client (the "core" client provides access to projects, teams, etc)
        self.client: GitClient = self.connection.clients_v7_1.get_git_client()
        self.project = project
        self.repository_id = repository_id

    def create_comment(self, pull_request_id: int, comment_id: int, text: str, **kwargs) -> Comment:
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
            **kwargs: Any additional keyword arguments.

        Returns:
            Comment: The response from the API.
        """
        return self.client.create_comment(
            comment=Comment(content=text),
            repository_id=self.repository_id,
            pull_request_id=pull_request_id,
            thread_id=comment_id,
            project=self.project,
            **kwargs,
        )

    def update_pr(self, pull_request_id, title=None, description=None, **kwargs) -> GitPullRequest:
        """
        Update a pull request.

        Args:
            pull_request_id (int): The Azure DevOps pull request ID.
            title (str): The title of the pull request.
            description (str): The description of the pull request.
            **kwargs: Any additional keyword arguments.

        Returns:
            GitPullRequest: The response from the API.
        """
        return self.client.update_pull_request(
            git_pull_request_to_update=GitPullRequest(title=title, description=description),
            repository_id=self.repository_id,
            project=self.project,
            pull_request_id=pull_request_id,
            **kwargs,
        )

    def read_all_text(
        self,
        path: str,
        commit_id: str = None,
        check_if_exists=True,
        **kwargs,
    ) -> str:
        """
        Read all text from a file.

        Args:
            path (str): The path to the file.
            commit_id (str): The commit ID.
            check_if_exists (bool): Whether to check if the file exists.
            **kwargs: Any additional keyword arguments.

        Returns:
            str: The text of the file.
        """
        try:
            byte_iterator = self.client.get_item_content(
                repository_id=self.repository_id,
                path=path,
                project=self.project,
                version_descriptor=GitVersionDescriptor(commit_id, version_type="commit") if commit_id else None,
                check_if_exists=check_if_exists,
                **kwargs,
            )
            return "".join(byte.decode("utf-8") for byte in byte_iterator).splitlines()
        except AzureDevOpsServiceError:
            # File Not Found
            return ""

    @staticmethod
    def process_comment_payload(payload: str) -> str:
        """
        Extract question from Service Bus payload.

        Args:
            payload (str): The Service Bus payload.

        Returns:
            str: The question from the Azure DevOps Comment.
        """
        return json.loads(payload)["resource"]["comment"]["content"]

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
        thread_context = self.client.get_pull_request_thread(
            repository_id=self.repository_id,
            pull_request_id=pull_request_id,
            thread_id=comment_id,
            project=self.project,
        ).thread_context

        commit_id = pull_request_event["pullRequest"]["lastMergeSourceCommit"]["commitId"]
        left, right = self._calculate_selection(thread_context, commit_id)

        return self._create_patch(left, right, thread_context.file_path)

    def _create_patch(self, left, right, file_path) -> List:
        """
        Create a patch.

        Args:
            left (List[str]): The left side of the diff.
            right (List[str]): The right side of the diff.
            file_path (str): The file path.

        Returns:
            List: The patch.
        """

        changes = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]

        for i, j in itertools.product(range(len(left)), range(len(right))):
            changes[i + 1][j + 1] = (
                changes[i][j] if left[i] == right[j] else 1 + min(changes[i][j + 1], changes[i + 1][j], changes[i][j])
            )

        patch = []
        line, row = len(left), len(right)
        while line > 0 and row > 0:
            if changes[line][row] <= changes[line - 1][row] and changes[line][row] <= changes[line][row - 1]:
                if left[line - 1] != right[row - 1]:
                    patch.extend((f"+ {right[row - 1]}", f"- {left[line - 1]}"))
                line -= 1
                row -= 1
            elif changes[line - 1][row] < changes[line][row - 1]:
                patch.append(f"- {left[line - 1]}")
                line -= 1
            else:
                patch.append(f"+ {right[row - 1]}")
                row -= 1

        patch.extend(f"- {left[i - 1]}" for i in range(0, line))
        patch.extend(f"+ {right[j - 1]}" for j in range(0, row))
        patch.append(file_path)
        patch.reverse()

        return patch

    def _calculate_selection(self, thread: GitPullRequestCommentThread, commit_id: str) -> Tuple[str, str]:
        """
        Calculate the selection for a given thread context.

        Args:
            thread (GitPullRequestCommentThread): The thread context.
            commit_id (str): The commit ID.

        Returns:
            Tuple[str, str]: The left and right selection.
        """

        original_content, changed_content = self._load_content(file_path=thread.file_path, commit_id_changed=commit_id)

        def get_selection(lines: str, line_start: int, line_end: int) -> str:
            return lines[line_start - 1 : line_end] if line_end - line_start >= C.MIN_CONTEXT_LINES else lines

        left_selection = (
            get_selection(original_content, thread.left_file_start.line, thread.left_file_end.line)
            if thread.left_file_start and thread.left_file_end
            else []
        )

        right_selection = (
            get_selection(changed_content, thread.right_file_start.line, thread.right_file_end.line)
            if thread.right_file_start and thread.right_file_end
            else []
        )

        return left_selection, right_selection

    def create_git_commit_ref_from_dict(self, commit_dict: Dict) -> GitCommitRef:
        """Create a GitCommitRef object from a dictionary.

        Args:
            commit_dict (Dict): The dictionary to create the GitCommitRef object from.

        Returns:
            GitCommitRef: The GitCommitRef object.
        """
        return GitCommitRef(commit_id=commit_dict["commitId"], url=commit_dict["url"])

    def create_git_pull_request_from_dict(self, pr_dict: Dict) -> GitPullRequest:
        """Create a GitPullRequest object from a dictionary.

        Args:
            pr_dict (Dict): The dictionary to create the GitPullRequest object from.

        Returns:
            GitPullRequest: The GitPullRequest object.
        """
        pull_request = GitPullRequest(
            title=pr_dict["title"],
            description=pr_dict["description"],
            source_ref_name=pr_dict["sourceRefName"],
            target_ref_name=pr_dict["targetRefName"],
            is_draft=pr_dict["isDraft"],
            reviewers=pr_dict["reviewers"],
            supports_iterations=pr_dict["supportsIterations"],
            artifact_id=pr_dict["artifactId"],
            status=pr_dict["status"],
            created_by=pr_dict["createdBy"],
            creation_date=pr_dict["creationDate"],
            last_merge_source_commit=pr_dict["lastMergeSourceCommit"],
            last_merge_target_commit=pr_dict["lastMergeTargetCommit"],
            last_merge_commit=pr_dict["lastMergeCommit"],
            url=pr_dict["url"],
            repository=pr_dict["repository"],
            merge_id=pr_dict["mergeId"],
        )
        pull_request.last_merge_source_commit = self.create_git_commit_ref_from_dict(
            pull_request.last_merge_source_commit
        )
        pull_request.last_merge_target_commit = self.create_git_commit_ref_from_dict(
            pull_request.last_merge_target_commit
        )
        pull_request.last_merge_commit = self.create_git_commit_ref_from_dict(pull_request.last_merge_commit)
        return pull_request

    def get_patches(self, pull_request_event) -> Iterable[List[str]]:
        """
        Get the patches for a given pull request event.

        Args:
            pull_request_event (Any): The pull request event to retrieve patches for.

        Returns:
            Iterable[List[str]]: An iterable of lists containing the patches for the pull request event.
        """

        if isinstance(pull_request_event, dict):
            pull_request = self.create_git_pull_request_from_dict(pull_request_event["pullRequest"])
        else:
            pull_request = pull_request_event

        git_changes = self._get_changed_blobs(pull_request)
        return [self._get_change(git_change, pull_request.last_merge_commit.commit_id) for git_change in git_changes]

    def _get_changed_blobs(self, pull_request: GitPullRequest) -> List[str]:
        """
        Get the changed blobs in a pull request.

        Args:
            pull_request (GitPullRequest): The pull request.

        Returns:
            List[Dict[str, str]]: The changed blobs.
        """
        changed_paths = []
        pr_commits = None

        skip = 0
        while pull_request.status != C.PR_TYPE_ABANDONED:
            pr_commits = self.client.get_commit_diffs(
                repository_id=self.repository_id,
                project=self.project,
                diff_common_commit=False,
                base_version_descriptor=GitBaseVersionDescriptor(
                    base_version=pull_request.last_merge_commit.commit_id, base_version_type="commit"
                ),
                target_version_descriptor=GitTargetVersionDescriptor(
                    target_version=pull_request.last_merge_target_commit.commit_id, target_version_type="commit"
                ),
            )
            changed_paths.extend([change for change in pr_commits.changes if "isFolder" not in change["item"]])
            skip += len(pr_commits.changes)
            if pr_commits.all_changes_included:
                break

        return changed_paths

    def _get_change(self, git_change, commit_id) -> List[str]:
        file_path = git_change["item"]["path"]

        original_content, changed_content = self._load_content(
            file_path, commit_id_original=git_change["item"]["commitId"], commit_id_changed=commit_id
        )

        patch = self._create_patch(original_content, changed_content, file_path)
        return "\n".join(patch)

    def _load_content(
        self,
        file_path,
        commit_id_original: str = None,
        commit_id_changed: str = None,
    ):
        return self.read_all_text(file_path, commit_id=commit_id_original), self.read_all_text(
            file_path, commit_id=commit_id_changed
        )


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
            link (str, optional): The link to the PR. Defaults to None.
            access_token (str, optional): The GitHub access token. Defaults to None.

        Returns:
            Dict[str, str]: The review.
        """
        link = os.getenv("LINK", link)
        access_token = os.getenv("ADO_TOKEN", access_token)

        if link and access_token:
            review = _summarize_files(diff)

            org, project, repo, pr_id = DevOpsClient._parse_url(link)

            DevOpsClient(pat=access_token, org=org, project=project, repository_id=repo).update_pr(
                pull_request_id=pr_id,
                description=review,
            )
            return {"response": "PR posted"}

        logging.warning("No PR to post too")
        return {"response": "No PR to post too"}

    @staticmethod
    def _parse_url(link):
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
        return org, project, repo, pr_id

    @staticmethod
    def get_pr_diff(patch_repo=None, patch_pr=None, access_token=None) -> str:
        """
        Get the diff of a PR.

        Args:
            patch_repo (str): The pointer to ADO in the format, org/project/repo
            patch_pr (str): The PR id.
            access_token (str): The ADO access token.
        """

        link = urllib.parse.unquote(
            os.getenv(
                "LINK",
                f"https://{patch_repo.split('/')[0]}.visualstudio.com/{patch_repo.split('/')[1]}/_git/{patch_repo.split('/')[2]}/pullrequest/{patch_pr}",
            )
        )

        access_token = os.getenv("ADO_TOKEN", access_token)

        if link and access_token:
            org, project, repo, pr_id = DevOpsClient._parse_url(link)

            client = DevOpsClient(pat=access_token, org=org, project=project, repository_id=repo)
            pull_request = client.client.get_pull_request_by_id(pull_request_id=pr_id)
            diff = client.get_patches(pull_request_event=pull_request)
            diff = "\n".join(diff)

            return {"response": "PR posted"}

        logging.warning("No PR to post too")
        return {"response": "No PR to post too"}


class DevOpsFunction(DevOpsClient):
    """Azure Function for process Service Messages from Azure DevOps."""

    def handle(self, msg) -> None:
        """
        The main function for the Azure Function.

        Args:
            msg (func.QueueMessage): The Service Bus message.
        """
        body = msg.get_body().decode("utf-8")
        logging.debug("Python ServiceBus queue trigger processed message: %s", body)
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
        logging.debug("Copilot Comment Alert Triggered")
        payload = json.loads(body)

        pr_id = self._get_pr_id(payload)
        comment_id = self._get_comment_id(payload)

        try:
            diff = self.get_patch(pull_request_event=payload["resource"], pull_request_id=pr_id, comment_id=comment_id)
        except Exception:
            diff = self.get_patches(pull_request_event=payload["resource"])

        logging.debug("Copilot diff: %s", diff)
        diff = "\n".join(diff)

        question = load_ask_yaml().format(diff=diff, ask=_DevOpsClient.process_comment_payload(body))

        response = _ask(question=question, max_tokens=1000)

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
        logging.debug("Copilot Commet ID: %s", comment_id)
        return comment_id

    def _process_summary(self, body) -> None:
        """
        Process a summary from Copilot.

        Args:
            body (str): The Service Bus payload.
        """
        logging.debug("Copilot Summary Alert Triggered")
        payload = json.loads(body)

        pr_id = self._get_pr_id(payload)
        link = self._get_link(pr_id)

        if "comment" in payload["resource"]:
            self._post_summary(payload, pr_id, link)

    def _get_link(self, pr_id) -> str:
        link = f"https://{self.org}.visualstudio.com/{self.project}/_git/{self.repository_id}/pullrequest/{pr_id}"
        logging.debug("Copilot Link: %s", link)
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
        logging.debug("Copilot PR ID: %s", pr_id)
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
        logging.debug("Copilot Commet ID: %s", comment_id)

        diff = self.get_patch(pull_request_event=payload["resource"], pull_request_id=pr_id, comment_id=comment_id)
        diff = "\n".join(diff)
        logging.debug("Copilot diff: %s", diff)

        self.post_pr_summary(diff, link=link)


def _review(repository=None, pull_request=None, diff: str = ".diff", link=None, access_token=None) -> Dict[str, str]:
    """Review Azure DevOps PR with Open AI, and post response as a comment.

    Args:
        link (str): The link to the PR.
        access_token (str): The Azure DevOps access token.

    Returns:
        Dict[str, str]: The response.
    """
    if repository and pull_request:
        diff_contents = DevOpsClient.get_pr_diff(repository, pull_request, access_token)
    else:
        with open(diff, "r", encoding="utf8") as file:
            diff_contents = file.read()

    return DevOpsClient.post_pr_summary(diff_contents, link, access_token)


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
