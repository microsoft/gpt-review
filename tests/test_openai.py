"""Tests for the Open AI Wrapper."""
import pytest
import os
import yaml
from openai.error import RateLimitError

from gpt_review._openai import _call_gpt, _get_engine
import gpt_review.constants as C


def get_engine_test() -> None:
    prompt = "This is a test prompt"

    AZURE_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../..", "azure.yaml")
    with open(AZURE_CONFIG_FILE) as f:
        AZURE_CONFIG = yaml.load(f, Loader=yaml.SafeLoader)

    engine = _get_engine(prompt=prompt, max_tokens=1000, fast=True)
    assert engine == AZURE_CONFIG.get("turbo_llm_model_deployment_id")

    engine = _get_engine(prompt=prompt, max_tokens=5000)
    assert engine == AZURE_CONFIG.get("smart_llm_model_deployment_id")

    engine = _get_engine(prompt=prompt, max_tokens=9000)
    assert engine == AZURE_CONFIG.get("large_llm_model_deployment_id")


def test_get_engine() -> None:
    get_engine_test()


@pytest.mark.integration
def test_int_get_engine() -> None:
    get_engine_test()


def rate_limit_test(monkeypatch):
    def mock_get_engine(prompt: str, max_tokens: int, fast: bool = False, large: bool = False):
        error = RateLimitError("Rate Limit Error")
        error.headers["Retry-After"] = 10
        raise error

    monkeypatch.setattr("gpt_review._openai._get_engine", mock_get_engine)
    with pytest.raises(RateLimitError):
        _call_gpt(prompt="This is a test prompt", retry=C.MAX_RETRIES)


def test_rate_limit(monkeypatch) -> None:
    rate_limit_test(monkeypatch)


@pytest.mark.integration
def test_int_rate_limit(monkeypatch) -> None:
    rate_limit_test(monkeypatch)
