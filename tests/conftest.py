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
