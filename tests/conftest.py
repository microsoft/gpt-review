import pytest
from collections import namedtuple


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
