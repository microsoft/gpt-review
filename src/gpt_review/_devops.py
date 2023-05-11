"""Azure DevOps API Wrappers."""
import json

import requests
from requests.models import Response


def _create_comment(
    token, org, project, repository_id, pull_request_id, comment_id, text, parentCommentId=0, commentType=1
) -> Response:
    """
    Create a comment on a pull request.

    Args:
        token (str): The Azure DevOps token.
        org (str): The Azure DevOps organization.
        project (str): The Azure DevOps project.
        repository_id (str): The Azure DevOps repository ID.
        pull_request_id (str): The Azure DevOps pull request ID.
        comment_id (str): The Azure DevOps comment ID.
        text (str): The text of the comment.
        parentCommentId (int, optional): The parent comment ID. Defaults to 0.
        commentType (int, optional): The comment type. Defaults to 1.

    Returns:
        Response: The response from the API.
    """
    url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}/threads/{comment_id}?api-version=6.0"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    data = {"comments": [{"parentCommentId": parentCommentId, "content": text, "commentType": commentType}]}

    return requests.post(url, headers=headers, data=json.dumps(data), timeout=10)


def _update_pr(token, org, project, repository_id, pull_request_id, title, description) -> Response:
    """
    Update a pull request.

    Args:
        token (str): The Azure DevOps token.
        org (str): The Azure DevOps organization.
        project (str): The Azure DevOps project.
        repository_id (str): The Azure DevOps repository ID.
        pull_request_id (str): The Azure DevOps pull request ID.
        title (str): The title of the pull request.
        description (str): The description of the pull request.

    Returns:
        Response: The response from the API.
    """
    url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}?api-version=6.0"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    data = {"title": title, "description": description}

    return requests.patch(url, headers=headers, data=json.dumps(data), timeout=10)


def _get_diff(token, org, project, repository_id, diff_common_commit, base_version, target_version) -> Response:
    """
    Get the diff between two commits.

    Args:
        token (str): The Azure DevOps token.
        org (str): The Azure DevOps organization.
        project (str): The Azure DevOps project.
        repository_id (str): The Azure DevOps repository ID.
        diff_common_commit (str): The common commit between the two versions.
        base_version (str): The base version.
        target_version (str): The target version.

    Returns:
        Response: The response from the API.
    """
    url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repository_id}/diffsCommonCommit/{diff_common_commit}?api-version=6.0"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    data = {"baseVersion": base_version, "targetVersion": target_version}

    return requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
