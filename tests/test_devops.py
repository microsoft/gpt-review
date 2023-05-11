import pytest
import requests_mock
from gpt_review._devops import _create_comment, _update_pr, _get_diff


PROJECT = "proj1"


@pytest.fixture
def mock_req():
    with requests_mock.Mocker() as m:
        yield m


def test_create_comment(mock_req) -> None:
    mock_req.post(
        "https://dev.azure.com/org1/proj1/_apis/git/repositories/repo1/pullrequests/pr1/threads/comment1?api-version=6.0",
        text="mock response",
    )
    response = _create_comment("token1", "org1", "proj1", "repo1", "pr1", "comment1", "text1")
    assert response.text == "mock response"


def test_update_pr(mock_req) -> None:
    mock_req.patch(
        "https://dev.azure.com/org1/proj1/_apis/git/repositories/repo1/pullrequests/pr1?api-version=6.0",
        text="mock response",
    )
    response = _update_pr("token1", "org1", "proj1", "repo1", "pr1", "title1", "description1")
    assert response.text == "mock response"


def test_get_diff(mock_req) -> None:
    mock_req.post(
        f"https://dev.azure.com/org1/{PROJECT}/_apis/git/repositories/repo1/diffsCommonCommit/commit1?api-version=6.0",
        text="mock response",
    )
    response = _get_diff("token1", "org1", PROJECT, "repo1", "commit1", "version1", "version2")
    assert response.text == "mock response"


@pytest.mark.integration
def test_create_comment_integration() -> None:
    response = _create_comment("token1", "org1", "proj1", "repo1", "pr1", "comment1", "text1")
    assert response.status_code == 203


@pytest.mark.integration
def test_update_pr_integration() -> None:
    response = _update_pr("token1", "org1", "proj1", "repo1", "pr1", "title1", "description1")
    assert response.status_code == 401


@pytest.mark.integration
def test_get_diff_integration() -> None:
    response = _get_diff("token1", "org1", "proj1", "repo1", "commit1", "version1", "version2")
    assert response.status_code == 404
