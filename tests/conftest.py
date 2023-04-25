import pytest
import yaml
from collections import namedtuple


@pytest.fixture
def small_report():
    """Load small.report.yaml file"""
    return load_report_config("small.config.yaml")


@pytest.fixture
def report_config():
    """Load sample.report.yaml file"""
    return load_report_config("sample.config.yaml")


def load_report_config(file_name):
    with open(file_name, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config["report"]


@pytest.fixture
def git_diff():
    """Load test.diff file"""
    with open("tests/test.diff", "r") as diff_file:
        diff = diff_file.read()
    return diff


@pytest.fixture
def config_yaml():
    with open("tests/test.config.yaml", encoding="utf8") as yaml_file:
        yield yaml_file


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
