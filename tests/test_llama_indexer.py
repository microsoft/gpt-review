"""Tests for the Llame Index Package."""
from gpt_review._ask import _load_azure_openai_context
from gpt_review._llama_index import _ask_doc


def test_ask_doc() -> None:
    _load_azure_openai_context()
    question = "What is the name of the package?"
    files = ["src/gpt_review/__init__.py"]
    _ask_doc(question, files)
