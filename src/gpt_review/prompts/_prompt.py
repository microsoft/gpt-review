"""Interface for a GPT Prompts."""
from dataclasses import dataclass
from typing import Self

from langchain.prompts import load_prompt, PromptTemplate

import gpt_review.constants as C


@dataclass
class LangChainPrompt(PromptTemplate):
    """A prompt for the GPT LangChain task."""

    prompt_yaml: str

    @classmethod
    def load(cls, prompt_yaml) -> Self:
        """Load the prompt."""
        return load_prompt(prompt_yaml)


def load_bug_yaml() -> LangChainPrompt:
    """Load the bug yaml."""
    return LangChainPrompt.load(C.BUG_PROMPT_YAML)


def load_coverage_yaml() -> LangChainPrompt:
    """Load the coverage yaml."""
    return LangChainPrompt.load(C.COVERAGE_PROMPT_YAML)


def load_summary_yaml() -> LangChainPrompt:
    """Load the summary yaml."""
    return LangChainPrompt.load(C.SUMMARY_PROMPT_YAML)
