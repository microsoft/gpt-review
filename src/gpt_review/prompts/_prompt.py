"""Interface for a GPT Prompts."""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from langchain.prompts import PromptTemplate, load_prompt

import gpt_review.constants as C

if sys.version_info[:2] <= (3, 10):
    from typing_extensions import Self
else:
    from typing import Self


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
    yaml_path = os.getenv("PROMPT_BUG", str(Path(__file__).parents[0].joinpath(C.BUG_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)


def load_coverage_yaml() -> LangChainPrompt:
    """Load the coverage yaml."""
    yaml_path = os.getenv("PROMPT_COVERAGE", str(Path(__file__).parents[0].joinpath(C.COVERAGE_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)


def load_summary_yaml() -> LangChainPrompt:
    """Load the summary yaml."""
    yaml_path = os.getenv("PROMPT_SUMMARY", str(Path(__file__).parents[0].joinpath(C.SUMMARY_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)
