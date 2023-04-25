import pytest
from collections import namedtuple


@pytest.fixture
def mock_openai(monkeypatch):
    """
    Mock OpenAI Functions with monkeypatch
    - aopenai.ChatCompletion.create
    """
    monkeypatch.setenv("OPENAI_API_KEY", "MOCK")
    monkeypatch.setenv("AZURE_OPENAI_API", "MOCK")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "MOCK")

    class MockResponse:
        def __init__(self):
            self.choices = [namedtuple("mockMessage", "message")(*[namedtuple("mockContent", "content")(*[["test"]])])]

    def mock_create(
        engine,
        messages,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty,
    ):
        return MockResponse()

    monkeypatch.setattr("openai.ChatCompletion.create", mock_create)
