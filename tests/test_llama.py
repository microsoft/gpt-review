"""Test cases for llama.py"""
import pytest

from simple_gpt.llama import detect_programming_language, detect_repo_language


@pytest.mark.integration
def test_llama_language_type_tests():
    languages = detect_programming_language("./tests", "index.tests.json")
    assert "Python" in languages
    assert len(languages) == 1


# @pytest.mark.integration
def test_llama_language_type_project():
    languages = detect_programming_language("./src/simple_gpt", "index.src.json")
    assert "Python" in languages
    assert len(languages) == 1


# @pytest.mark.integration
def test_repo_summary():
    languages = detect_repo_language("dciborow", "action-gpt")
    assert len(languages) != 0
