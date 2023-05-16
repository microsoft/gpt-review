from collections import namedtuple

import pytest
import yaml
from llama_index import SimpleDirectoryReader


def pytest_collection_modifyitems(items):
    for item in items:
        if "_int_" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "_cli_" in item.nodeid:
            item.add_marker(pytest.mark.cli)
        else:
            item.add_marker(pytest.mark.unit)


@pytest.fixture
def mock_openai(monkeypatch) -> None:
    """
    Mock OpenAI Functions with monkeypatch
    - aopenai.ChatCompletion.create
    """
    monkeypatch.setenv("OPENAI_API_KEY", "MOCK")
    monkeypatch.setenv("AZURE_OPENAI_API", "MOCK")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "MOCK")
    monkeypatch.setenv("FILE_SUMMARY_FULL", "true")

    class MockResponse:
        def __init__(self) -> None:
            self.choices = [namedtuple("mockMessage", "message")(*[namedtuple("mockContent", "content")(*[["test"]])])]

    class MockQueryResponse:
        def __init__(self) -> None:
            self.response = "test"

    class MockStorageContext:
        def persist(self, persist_dir) -> None:
            pass

    class MockIndex:
        def __init__(self) -> None:
            self.storage_context = MockStorageContext()

        def query(self, question: str) -> MockQueryResponse:
            assert isinstance(question, str)
            return MockQueryResponse()

        def as_query_engine(self):
            return self

    def mock_create(
        model=None,
        deployment_id=None,
        messages=None,
        temperature=0,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    ) -> MockResponse:
        return MockResponse()

    def from_documents(documents, service_context=None) -> MockIndex:
        return MockIndex()

    def init_mock_reader(self, owner, repo, use_parser) -> None:
        pass

    def mock_load_data_from_branch(self, branch):
        return SimpleDirectoryReader(input_dir=".").load_data()

    monkeypatch.setattr("openai.ChatCompletion.create", mock_create)
    monkeypatch.setattr("llama_index.GPTVectorStoreIndex.from_documents", from_documents)
    monkeypatch.setattr("llama_index.GithubRepositoryReader.__init__", init_mock_reader)
    monkeypatch.setattr("llama_index.GithubRepositoryReader._load_data_from_branch", mock_load_data_from_branch)

    def mock_query(self, question) -> MockQueryResponse:
        return MockQueryResponse()

    monkeypatch.setattr("llama_index.indices.query.base.BaseQueryEngine.query", mock_query)


@pytest.fixture
def mock_github(monkeypatch) -> None:
    """
    Mock GitHub Functions with monkeypatch
    - requests.get
    """
    monkeypatch.setenv("LINK", "https://github.com/microsoft/gpt-review/pull/1")
    monkeypatch.setenv("GIT_COMMIT_HASH", "a9da0c1e65f1102bc2ae16abed7b6a66400a5bde")

    class MockResponse:
        def __init__(self) -> None:
            self.text = "diff --git a/README.md b/README.md"

        def json(self) -> dict:
            return {"test": "test"}

    def mock_get(url, headers, timeout) -> MockResponse:
        return MockResponse()

    def mock_put(url, headers, data, timeout) -> MockResponse:
        return MockResponse()

    def mock_post(url, headers, data, timeout) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.put", mock_put)
    monkeypatch.setattr("requests.post", mock_post)


@pytest.fixture
def mock_github_comment(monkeypatch) -> None:
    class MockCommentResponse:
        def json(self) -> list:
            return [
                {
                    "user": {"login": "github-actions[bot]"},
                    "body": "Summary by GPT-4",
                    "id": 1,
                }
            ]

    def mock_get(url, headers, timeout) -> MockCommentResponse:
        return MockCommentResponse()

    monkeypatch.setattr("requests.get", mock_get)


@pytest.fixture
def mock_git_commit(monkeypatch) -> None:
    """Mock git.commit with pytest monkey patch"""

    class MockGit:
        def __init__(self) -> None:
            self.git = self

        def commit(self, message, push: bool = False) -> str:
            return "test commit response"

        def diff(self, message, cached) -> str:
            return "test diff response"

        def push(self) -> str:
            return "test push response"

    def mock_init(cls) -> MockGit:
        return MockGit()

    monkeypatch.setattr("git.repo.Repo.init", mock_init)


@pytest.fixture
def report_config():
    """Load sample.report.yaml file"""
    return load_report_config("config.summary.template.yml")


def load_report_config(file_name):
    with open(file_name, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config["report"]


@pytest.fixture
def config_yaml():
    return "tests/config.summary.test.yml"


@pytest.fixture
def git_diff() -> str:
    """Load test.diff file"""
    with open("tests/mock.diff", "r") as diff_file:
        diff = diff_file.read()
    return diff


@pytest.fixture
def empty_summary(monkeypatch) -> None:
    """Test empty summary."""
    monkeypatch.setenv("FILE_SUMMARY", "false")
    monkeypatch.setenv("TEST_SUMMARY", "false")
    monkeypatch.setenv("BUG_SUMMARY", "false")
    monkeypatch.setenv("RISK_SUMMARY", "false")
    monkeypatch.setenv("FULL_SUMMARY", "false")


@pytest.fixture
def file_summary(monkeypatch) -> None:
    """Test empty summary."""
    monkeypatch.setenv("FILE_SUMMARY_FULL", "false")
