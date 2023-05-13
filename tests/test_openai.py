"""Tests for the Open AI Wrapper."""
import pytest
from openai.error import RateLimitError

import gpt_review.constants as C
from gpt_review._openai import _call_gpt, _get_model
from gpt_review.context import _load_azure_openai_context


def get_model_test() -> None:
    prompt = "This is a test prompt"

    context = _load_azure_openai_context()

    model = _get_model(prompt=prompt, max_tokens=1000, fast=True)
    assert model == context.turbo_llm_model_deployment_id

    model = _get_model(prompt=prompt, max_tokens=5000)
    assert model == context.smart_llm_model_deployment_id

    model = _get_model(prompt=prompt, max_tokens=9000)
    assert model == context.large_llm_model_deployment_id


def test_get_model() -> None:
    get_model_test()


@pytest.mark.integration
def test_int_get_model() -> None:
    get_model_test()


def rate_limit_test(monkeypatch):
    def mock_get_model(prompt: str, max_tokens: int, fast: bool = False, large: bool = False):
        error = RateLimitError("Rate Limit Error")
        error.headers["Retry-After"] = 10
        raise error

    monkeypatch.setattr("gpt_review._openai._get_model", mock_get_model)
    with pytest.raises(RateLimitError):
        _call_gpt(prompt="This is a test prompt", retry=C.MAX_RETRIES)


def test_rate_limit(monkeypatch) -> None:
    rate_limit_test(monkeypatch)


@pytest.mark.integration
def test_int_rate_limit(monkeypatch) -> None:
    rate_limit_test(monkeypatch)
