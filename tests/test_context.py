"""Tests for the context grabber."""
from gpt_review.context import _load_context_file


def test_load_context_file(monkeypatch) -> None:
    monkeypatch.setenv("CONTEXT_FILE", "azure.yaml.template")
    yaml_context = _load_context_file()
    assert "azure_api_type" in yaml_context
    assert "azure_api_base" in yaml_context
    assert "azure_api_version" in yaml_context
