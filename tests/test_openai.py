"""Tests for the Open AI Wrapper."""
import pytest
from gpt_review._openai import _get_engine


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
