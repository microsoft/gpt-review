"""Tests for the Llame Index Package."""
import pytest

from gpt_review._ask import _load_azure_openai_context
from gpt_review._llama_index import _ask_doc


def ask_doc_test() -> None:
    _load_azure_openai_context()
    question = "What is the name of the package?"
    files = ["src/gpt_review/__init__.py"]
    _ask_doc(question, files, fast=True)


def test_ask_doc(mock_openai) -> None:
    """Unit Test for the ask_doc function."""
    ask_doc_test()


@pytest.mark.integration
def test_int_ask_doc() -> None:
    """Integration Test for the ask_doc function."""
    ask_doc_test()
