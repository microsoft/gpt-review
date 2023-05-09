"""Tests for the Open AI Wrapper."""
import pytest
from openai.error import RateLimitError

from gpt_review._openai import _call_gpt, _get_engine
import gpt_review.constants as C


def get_engine_test() -> None:
    prompt = "This is a test prompt"

    engine = _get_engine(prompt=prompt, max_tokens=1000, fast=True)
    assert engine == "gpt-35-turbo"

    engine = _get_engine(prompt=prompt, max_tokens=5000)
    assert engine == "gpt-4"

    engine = _get_engine(prompt=prompt, max_tokens=9000)
    assert engine == "gpt-4-32k"


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
