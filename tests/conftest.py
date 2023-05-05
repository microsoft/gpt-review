import os
import pytest
from collections import namedtuple

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


@pytest.fixture
def mock_openai(monkeypatch) -> None:
    """
    Mock OpenAI Functions with monkeypatch
    - aopenai.ChatCompletion.create
    """
    monkeypatch.setenv("OPENAI_API_KEY", "MOCK")
    monkeypatch.setenv("AZURE_OPENAI_API", "MOCK")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "MOCK")

    class MockResponse:
        def __init__(self) -> None:
            self.choices = [namedtuple("mockMessage", "message")(*[namedtuple("mockContent", "content")(*[["test"]])])]

    class MockQueryResponse:
        def __init__(self) -> None:
            self.response = "test"

    class MockIndex:
        def query(self, question: str) -> MockQueryResponse:
            assert isinstance(question, str)
            return MockQueryResponse()

        def as_query_engine(self):
            return self

    def mock_create(
        engine,
        messages,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty,
    ) -> MockResponse:
        return MockResponse()

    def from_documents(documents, service_context=None) -> MockIndex:
        return MockIndex()

    monkeypatch.setattr("openai.ChatCompletion.create", mock_create)
    monkeypatch.setattr("llama_index.GPTVectorStoreIndex.from_documents", from_documents)


@pytest.fixture
def mock_github(monkeypatch) -> None:
    """
    Mock GitHub Functions with monkeypatch
    - requests.get
    """

    class MockResponse:
        def __init__(self) -> None:
            self.text = "diff --git a/README.md b/README.md"

        def json(self) -> dict:
            return {"test": "test"}

    def mock_get(url, headers, timeout) -> MockResponse:
        return MockResponse()

    def mock_put(url, headers, timeout) -> MockResponse:
        return MockResponse()

    def mock_post(url, headers, data, timeout) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.put", mock_put)
    monkeypatch.setattr("requests.post", mock_post)


@pytest.fixture
def mock_git_commit(monkeypatch) -> None:
    """Mock git.commit with pytest monkey patch"""

    class MockGit:
        def __init__(self) -> None:
            self.git = self

        def commit(self, message) -> str:
            return "test commit response"

        def diff(self, message, cached) -> str:
            return "test diff response"

    def mock_init(cls):
        return MockGit()

    monkeypatch.setattr("git.repo.Repo.init", mock_init)


@pytest.fixture
def mock_devops(monkeypatch) -> None:
    """
    Mock Azure DevOps Functions with monkeypatch
    - requests.get
    """

    class MockResponse:
        def __init__(self) -> None:
            self.text = "diff --git a/README.md b/README.md"
            self.status_code = 200

        def json(self) -> dict:
            return {
                "test": "test",
                "sourceRefName": "refs/heads/main",
                "targetRefName": "refs/heads/pipeline-test",
                "changes": [
                    {
                        "item": {
                            "gitObjectType": "tree",
                            "commitId": "23d0bc5b128a10056dc68afece360d8a0fabb014",
                            "path": "/CustomerAddressModule",
                            "isFolder": True,
                            "url": "https://dev.azure.com/fabrikam/c34d5807-1734-4541-ad1c-d16e9ac1faca/_apis/git/repositories/278d5cd2-584d-4b63-824a-2ba458937249/items/CustomerAddressModule?versionType=Commit&version=23d0bc5b128a10056dc68afece360d8a0fabb014"
                        },
                        "changeType": "add"
                    }
                ]
            }

    def mock_get(url, headers, timeout) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setenv("AZURE_DEVOPS_ORGANIZATION", "MOCKVALUE")
    monkeypatch.setenv("AZURE_DEVOPS_PROJECT", "MOCKVALUE")
    monkeypatch.setenv("AZURE_DEVOPS_REPOSITORY", "MOCKVALUE")
    monkeypatch.setenv("AZURE_DEVOPS_PULL_REQUEST", "MOCKVALUE")
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", "MOCKVALUE")


@pytest.fixture
def devops_creds(monkeypatch) -> None:
    """
    Set the Azure DevOps credentials from Key Vault:
    """
    kv_client = SecretClient(
        vault_url=os.getenv("AZURE_KEY_VAULT_URL", DEFAULT_KEY_VAULT), credential=DefaultAzureCredential()
    )
    monkeypatch.setenv("AZURE_DEVOPS_ORGANIZATION", kv_client.get_secret("azure-devops-organization").value)
    monkeypatch.setenv("AZURE_DEVOPS_PROJECT", kv_client.get_secret("azure-devops-project").value)
    monkeypatch.setenv("AZURE_DEVOPS_REPOSITORY", kv_client.get_secret("azure-devops-repository").value)
    monkeypatch.setenv("AZURE_DEVOPS_PULL_REQUEST", kv_client.get_secret("azure-devops-pull-request").value)
    monkeypatch.setenv("AZURE_DEVOPS_TOKEN", kv_client.get_secret("azure-devops-token").value)
