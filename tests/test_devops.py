import os
from dataclasses import dataclass

import pytest
import requests_mock
from azure.devops.v7_1.git.models import (
    Comment,
    CommentThreadContext,
    GitBaseVersionDescriptor,
    GitCommitDiffs,
    GitPullRequest,
    GitPullRequestCommentThread,
    GitTargetVersionDescriptor,
)

from gpt_review.repositories.devops import DevOpsClient, DevOpsFunction, _comment

# Azure Devops PAT requires
# - Code: 'Read','Write'
# - Pull Request Threads: 'Read & Write'
TOKEN = os.getenv("ADO_TOKEN", "token1")

ORG = os.getenv("ADO_ORG", "msazure")
PROJECT = os.getenv("ADO_PROJECT", "one")
REPO = os.getenv("ADO_REPO", "azure-gaming")
PR_ID = int(os.getenv("ADO_PR_ID", 8063875))
COMMENT_ID = int(os.getenv("ADO_COMMENT_ID", 141344325))

SOURCE = os.getenv("ADO_COMMIT_SOURCE", "36f9a015ee220516f5f553faaa1898ab10972536")
TARGET = os.getenv("ADO_COMMIT_TARGET", "ecea1ea7db038317e94b45e090781410dc519b85")

SAMPLE_PAYLOAD = """{
  "resource": {
    "comment": {
      "content": "copilot: summary of this changed code"
    }
  }
}
"""

LONG_PAYLOAD = {
    "id": "e89fa09c-f412-4167-a2cd-f6a5bb8aef56",
    "eventType": "ms.vss-code.git-pullrequest-comment-event",
    "publisherId": "tfs",
    "message": {"text": "Daniel Ciborowski has replied to a pull request comment"},
    "detailedMessage": {
        "text": 'Daniel Ciborowski has replied to a pull request comment\r\n```suggestion\n              inlineScript: |                \n                echo "##[section] Summarize Pull Request with Open AI"\n\n                echo "##[command]python3 -m pip install --upgrade pip"\n                python3 -m pip install --upgrade pip --quiet\n```\nhow could i update this code?\r\n'
    },
    "resource": {
        "comment": {
            "id": 2,
            "parentCommentId": 1,
            "author": {
                "displayName": "Daniel Ciborowski",
                "url": "https://spsprodwus23.vssps.visualstudio.com/A41b4f3ee-c651-4a14-9847-b7cbb5315b80/_apis/Identities/0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "_links": {
                    "avatar": {
                        "href": "https://msazure.visualstudio.com/_apis/GraphProfile/MemberAvatars/aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4"
                    }
                },
                "id": "0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "uniqueName": "dciborow@microsoft.com",
                "imageUrl": "https://msazure.visualstudio.com/_apis/GraphProfile/MemberAvatars/aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4",
                "descriptor": "aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4",
            },
            "content": '```suggestion\n              inlineScript: |                \n                echo "##[section] Summarize Pull Request with Open AI"\n\n                echo "##[command]python3 -m pip install --upgrade pip"\n                python3 -m pip install --upgrade pip --quiet\n```\nhow could i update this code?',
            "publishedDate": "2023-05-13T00:30:56.68Z",
            "lastUpdatedDate": "2023-05-13T00:30:56.68Z",
            "lastContentUpdatedDate": "2023-05-13T00:30:56.68Z",
            "commentType": "text",
            "usersLiked": [],
            "_links": {
                "self": {
                    "href": "https://msazure.visualstudio.com/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/pullRequests/8063875/threads/141415813/comments/2"
                },
                "repository": {
                    "href": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3"
                },
                "threads": {
                    "href": "https://msazure.visualstudio.com/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/pullRequests/8063875/threads/141415813"
                },
                "pullRequests": {"href": "https://msazure.visualstudio.com/_apis/git/pullRequests/8063875"},
            },
        },
        "pullRequest": {
            "repository": {
                "id": "612d9367-8ab6-4929-abe6-b5b5ad7b5ad3",
                "name": "Azure-Gaming",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3",
                "project": {
                    "id": "b32aa71e-8ed2-41b2-9d77-5bc261222004",
                    "name": "One",
                    "description": "MSAzure/One is the VSTS project containing all Azure team code bases and work items.\nPlease see https://aka.ms/azaccess for work item and source access policies.",
                    "url": "https://msazure.visualstudio.com/_apis/projects/b32aa71e-8ed2-41b2-9d77-5bc261222004",
                    "state": "wellFormed",
                    "revision": 307061,
                    "visibility": "organization",
                    "lastUpdateTime": "2023-05-12T17:40:59.963Z",
                },
                "size": 508859977,
                "remoteUrl": "https://msazure.visualstudio.com/DefaultCollection/One/_git/Azure-Gaming",
                "sshUrl": "msazure@vs-ssh.visualstudio.com:v3/msazure/One/Azure-Gaming",
                "webUrl": "https://msazure.visualstudio.com/DefaultCollection/One/_git/Azure-Gaming",
                "isDisabled": False,
                "isInMaintenance": False,
            },
            "pullRequestId": 8063875,
            "codeReviewId": 8836473,
            "status": "active",
            "createdBy": {
                "displayName": "Daniel Ciborowski",
                "url": "https://spsprodwus23.vssps.visualstudio.com/A41b4f3ee-c651-4a14-9847-b7cbb5315b80/_apis/Identities/0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "_links": {
                    "avatar": {
                        "href": "https://msazure.visualstudio.com/_apis/GraphProfile/MemberAvatars/aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4"
                    }
                },
                "id": "0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "uniqueName": "dciborow@microsoft.com",
                "imageUrl": "https://msazure.visualstudio.com/_api/_common/identityImage?id=0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "descriptor": "aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4",
            },
            "creationDate": "2023-05-05T03:11:26.8599393Z",
            "title": "Sample PR Title",
            "description": "description1",
            "sourceRefName": "refs/heads/dciborow/update-pr",
            "targetRefName": "refs/heads/main",
            "mergeStatus": "succeeded",
            "isDraft": False,
            "mergeId": "0e7397c6-5f11-402c-a5c6-c5a12b105350",
            "lastMergeSourceCommit": {
                "commitId": "ecea1ea7db038317e94b45e090781410dc519b85",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/commits/ecea1ea7db038317e94b45e090781410dc519b85",
            },
            "lastMergeTargetCommit": {
                "commitId": "36f9a015ee220516f5f553faaa1898ab10972536",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/commits/36f9a015ee220516f5f553faaa1898ab10972536",
            },
            "lastMergeCommit": {
                "commitId": "d5fc735b618647a78a0aff006445b67bfe4e8185",
                "author": {
                    "name": "Daniel Ciborowski",
                    "email": "dciborow@microsoft.com",
                    "date": "2023-05-05T14:23:49Z",
                },
                "committer": {
                    "name": "Daniel Ciborowski",
                    "email": "dciborow@microsoft.com",
                    "date": "2023-05-05T14:23:49Z",
                },
                "comment": "Merge pull request 8063875 from dciborow/update-pr into main",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/commits/d5fc735b618647a78a0aff006445b67bfe4e8185",
            },
            "reviewers": [],
            "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/pullRequests/8063875",
            "supportsIterations": True,
            "artifactId": "vstfs:///Git/PullRequestId/b32aa71e-8ed2-41b2-9d77-5bc261222004%2f612d9367-8ab6-4929-abe6-b5b5ad7b5ad3%2f8063875",
        },
    },
    "resourceVersion": "2.0",
    "resourceContainers": {
        "collection": {"id": "41bf5486-7392-4b7a-a7e3-a735c767e3b3", "baseUrl": "https://msazure.visualstudio.com/"},
        "account": {"id": "41b4f3ee-c651-4a14-9847-b7cbb5315b80", "baseUrl": "https://msazure.visualstudio.com/"},
        "project": {"id": "b32aa71e-8ed2-41b2-9d77-5bc261222004", "baseUrl": "https://msazure.visualstudio.com/"},
    },
    "createdDate": "2023-05-13T00:31:02.6421816Z",
}

PR_COMMENT_PAYLOAD = {
    "id": "851991af-ce4b-4463-83d4-eb4733559f14",
    "eventType": "ms.vss-code.git-pullrequest-comment-event",
    "publisherId": "tfs",
    "message": {"text": "Daniel Ciborowski has replied to a pull request comment"},
    "detailedMessage": {"text": "Daniel Ciborowski has replied to a pull request comment\r\ncopilot: test\r\n"},
    "resource": {
        "comment": {
            "id": 5,
            "parentCommentId": 1,
            "author": {
                "displayName": "Daniel Ciborowski",
                "url": "https://spsprodwus23.vssps.visualstudio.com/A41b4f3ee-c651-4a14-9847-b7cbb5315b80/_apis/Identities/0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "_links": {
                    "avatar": {
                        "href": "https://msazure.visualstudio.com/_apis/GraphProfile/MemberAvatars/aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4"
                    }
                },
                "id": "0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "uniqueName": "dciborow@microsoft.com",
                "imageUrl": "https://msazure.visualstudio.com/_apis/GraphProfile/MemberAvatars/aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4",
                "descriptor": "aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4",
            },
            "content": "copilot: test",
            "publishedDate": "2023-05-16T01:22:28.67Z",
            "lastUpdatedDate": "2023-05-16T01:22:28.67Z",
            "lastContentUpdatedDate": "2023-05-16T01:22:28.67Z",
            "commentType": "text",
            "usersLiked": [],
            "_links": {
                "self": {
                    "href": "https://msazure.visualstudio.com/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/pullRequests/8111242/threads/141607999/comments/5"
                },
                "repository": {
                    "href": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3"
                },
                "threads": {
                    "href": "https://msazure.visualstudio.com/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/pullRequests/8111242/threads/141607999"
                },
                "pullRequests": {"href": "https://msazure.visualstudio.com/_apis/git/pullRequests/8111242"},
            },
        },
        "pullRequest": {
            "repository": {
                "id": "612d9367-8ab6-4929-abe6-b5b5ad7b5ad3",
                "name": "Azure-Gaming",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3",
                "project": {
                    "id": "b32aa71e-8ed2-41b2-9d77-5bc261222004",
                    "name": "One",
                    "description": "MSAzure/One is the VSTS project containing all Azure team code bases and work items.\nPlease see https://aka.ms/azaccess for work item and source access policies.",
                    "url": "https://msazure.visualstudio.com/_apis/projects/b32aa71e-8ed2-41b2-9d77-5bc261222004",
                    "state": "wellFormed",
                    "revision": 307071,
                    "visibility": "organization",
                    "lastUpdateTime": "2023-05-15T17:47:30.807Z",
                },
                "size": 508859977,
                "remoteUrl": "https://msazure.visualstudio.com/DefaultCollection/One/_git/Azure-Gaming",
                "sshUrl": "msazure@vs-ssh.visualstudio.com:v3/msazure/One/Azure-Gaming",
                "webUrl": "https://msazure.visualstudio.com/DefaultCollection/One/_git/Azure-Gaming",
                "isDisabled": False,
                "isInMaintenance": False,
            },
            "pullRequestId": 8111242,
            "codeReviewId": 8886256,
            "status": "active",
            "createdBy": {
                "displayName": "Daniel Ciborowski",
                "url": "https://spsprodwus23.vssps.visualstudio.com/A41b4f3ee-c651-4a14-9847-b7cbb5315b80/_apis/Identities/0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "_links": {
                    "avatar": {
                        "href": "https://msazure.visualstudio.com/_apis/GraphProfile/MemberAvatars/aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4"
                    }
                },
                "id": "0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "uniqueName": "dciborow@microsoft.com",
                "imageUrl": "https://msazure.visualstudio.com/_api/_common/identityImage?id=0ef5b3af-3e01-48fd-9bd3-2f701c8fdebe",
                "descriptor": "aad.OTgwYzcxNzEtMDI2Ni03YzVmLTk0YzEtMDNlYzU2YjViYjY4",
            },
            "creationDate": "2023-05-15T03:32:53.2319611Z",
            "title": "Added __init__.py",
            "description": "Added __init__.py",
            "sourceRefName": "refs/heads/dciborow/python-sample",
            "targetRefName": "refs/heads/main",
            "mergeStatus": "succeeded",
            "isDraft": False,
            "mergeId": "762c15e2-0877-45d3-bec1-4257f94438b1",
            "lastMergeSourceCommit": {
                "commitId": "b7017e51b312116557fa2769a4a8e5310c9d51f4",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/commits/b7017e51b312116557fa2769a4a8e5310c9d51f4",
            },
            "lastMergeTargetCommit": {
                "commitId": "36f9a015ee220516f5f553faaa1898ab10972536",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/commits/36f9a015ee220516f5f553faaa1898ab10972536",
            },
            "lastMergeCommit": {
                "commitId": "84a8d5cc827b85271dda7f865c8516ddcc2ba941",
                "author": {
                    "name": "Daniel Ciborowski",
                    "email": "dciborow@microsoft.com",
                    "date": "2023-05-15T03:54:44Z",
                },
                "committer": {
                    "name": "Daniel Ciborowski",
                    "email": "dciborow@microsoft.com",
                    "date": "2023-05-15T03:54:44Z",
                },
                "comment": "Merge pull request 8111242 from dciborow/python-sample into main",
                "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/commits/84a8d5cc827b85271dda7f865c8516ddcc2ba941",
            },
            "reviewers": [],
            "url": "https://msazure.visualstudio.com/b32aa71e-8ed2-41b2-9d77-5bc261222004/_apis/git/repositories/612d9367-8ab6-4929-abe6-b5b5ad7b5ad3/pullRequests/8111242",
            "supportsIterations": True,
            "artifactId": "vstfs:///Git/PullRequestId/b32aa71e-8ed2-41b2-9d77-5bc261222004%2f612d9367-8ab6-4929-abe6-b5b5ad7b5ad3%2f8111242",
        },
    },
    "resourceVersion": "2.0",
    "resourceContainers": {
        "collection": {"id": "41bf5486-7392-4b7a-a7e3-a735c767e3b3", "baseUrl": "https://msazure.visualstudio.com/"},
        "account": {"id": "41b4f3ee-c651-4a14-9847-b7cbb5315b80", "baseUrl": "https://msazure.visualstudio.com/"},
        "project": {"id": "b32aa71e-8ed2-41b2-9d77-5bc261222004", "baseUrl": "https://msazure.visualstudio.com/"},
    },
    "createdDate": "2023-05-16T01:22:34.9492237Z",
}


@pytest.fixture
def mock_req():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def mock_ado_client(monkeypatch) -> None:
    monkeypatch.setenv("ADO_TOKEN", "MOCK_TOKEN")

    @dataclass
    class MockResponse:
        text: str
        status_code: int = 203

    def mock_update_thread(self, text, repository_id, pull_request_id, comment_id) -> MockResponse:
        return MockResponse("mock response")

    monkeypatch.setattr("azure.devops.v7_1.git.git_client_base.GitClientBase.update_thread", mock_update_thread)

    class MockDevOpsClient:
        def get_git_client(self) -> "MockDevOpsClient":
            return MockDevOpsClient()

        def update_thread(self, text, repository_id, pull_request_id, comment_id) -> MockResponse:
            return MockResponse("mock response")

        def create_comment(self, comment, repository_id, pull_request_id, thread_id, project=None) -> Comment:
            return Comment()

        def get_pull_request_thread(
            self, repository_id, pull_request_id, thread_id, project=None, iteration=None, base_iteration=None
        ) -> GitPullRequestCommentThread:
            return GitPullRequestCommentThread(thread_context=CommentThreadContext())

        def update_pull_request(
            self, git_pull_request_to_update, repository_id, pull_request_id, project=None
        ) -> GitPullRequest:
            return GitPullRequest()

        def get_item_content(self, repository_id="", path="", project="", version_descriptor=None, **kwargs):
            return bytes("mock content", "utf-8").split()

        def get_commit_diffs(
            self,
            repository_id="",
            project=None,
            diff_common_commit=None,
            top=None,
            skip=None,
            base_version_descriptor=None,
            target_version_descriptor=None,
            base_version=None,
            target_version=None,
        ) -> GitCommitDiffs:
            return GitCommitDiffs(changes=[], all_changes_included=True)

    def mock_client(self) -> MockDevOpsClient:
        return MockDevOpsClient()

    monkeypatch.setattr("azure.devops.released.client_factory.ClientFactory.get_core_client", mock_client)
    monkeypatch.setattr("azure.devops.v7_1.client_factory.ClientFactoryV7_1.get_git_client", mock_client)


@pytest.fixture
def devops_client() -> DevOpsClient:
    return DevOpsClient(TOKEN, ORG, PROJECT, REPO)


@pytest.fixture
def devops_function() -> DevOpsFunction:
    return DevOpsFunction(TOKEN, ORG, PROJECT, REPO)


def test_create_comment(mock_ado_client: None, devops_client: DevOpsClient) -> None:
    response = devops_client.create_comment(pull_request_id=PR_ID, comment_id=COMMENT_ID, text="text1")
    assert isinstance(response, Comment)


def test_update_pr(mock_ado_client: None, devops_client: DevOpsClient) -> None:
    response = devops_client.update_pr(pull_request_id=PR_ID, title="title1", description="description1")
    assert isinstance(response, GitPullRequest)


@pytest.mark.integration
def test_int_create_comment(devops_client: DevOpsClient) -> None:
    response = devops_client.create_comment(pull_request_id=PR_ID, comment_id=COMMENT_ID, text="text1")
    assert isinstance(response, Comment)


@pytest.mark.integration
def test_int_update_pr(devops_client: DevOpsClient) -> None:
    response = devops_client.update_pr(PR_ID, description="description1")
    assert isinstance(response, GitPullRequest)
    response = devops_client.update_pr(PR_ID, title="Sample PR Title")
    assert isinstance(response, GitPullRequest)


def process_payload_test() -> None:
    question = DevOpsClient.process_comment_payload(SAMPLE_PAYLOAD)
    link = "https://msazure.visualstudio.com/One/_git/Azure-Gaming/pullrequest/8063875"
    _comment(question, comment_id=COMMENT_ID, link=link)


def test_process_payload(mock_openai: None, mock_ado_client: None) -> None:
    process_payload_test()


@pytest.mark.integration
def test_int_process_payload() -> None:
    process_payload_test()


def get_patch_test(devops_client: DevOpsClient, expected_len: int) -> None:
    comment_id = LONG_PAYLOAD["resource"]["comment"]["_links"]["threads"]["href"].split("/")[-1]
    patch = devops_client.get_patch(
        pull_request_event=LONG_PAYLOAD["resource"], pull_request_id=PR_ID, comment_id=comment_id
    )
    assert len(patch) == expected_len


def test_get_patch(mock_openai: None, mock_ado_client: None, devops_client: DevOpsClient) -> None:
    get_patch_test(devops_client, 1)


@pytest.mark.integration
def test_int_get_patch(devops_client: DevOpsClient) -> None:
    get_patch_test(devops_client, 64)


def get_patch_pr_comment_test(devops_function: DevOpsFunction, expected_len: int) -> None:
    patch = devops_function.get_patches(pull_request_event=PR_COMMENT_PAYLOAD["resource"])
    patch = "\n".join(patch)
    assert len(patch.splitlines()) == expected_len


def test_get_patch_pr_comment(mock_openai: None, mock_ado_client: None, devops_function: DevOpsFunction) -> None:
    get_patch_pr_comment_test(devops_function, 0)


@pytest.mark.integration
def test_int_get_patch_pr_comment(devops_function: DevOpsFunction) -> None:
    get_patch_pr_comment_test(devops_function, 3079)
