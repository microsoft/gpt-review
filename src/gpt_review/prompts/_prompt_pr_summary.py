"""Prompt for PR summarization."""
import os
from pathlib import Path
from gpt_review.prompts._prompt import LangChainPrompt
import gpt_review.constants as C


def load_pr_summary_yaml() -> LangChainPrompt:
    """Load the PR summary yaml."""
    yaml_path = os.getenv("PROMPT_PR_SUMMARY", str(Path(__file__).parents[0].joinpath(C.PR_SUMMARY_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)


def load_pr_review_yaml() -> LangChainPrompt:
    """Load the PR review yaml."""
    yaml_path = os.getenv("PROMPT_PR_REVIEW", str(Path(__file__).parents[0].joinpath(C.PR_REVIEW_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)


def load_batch_pr_summary_yaml() -> LangChainPrompt:
    """Load the PR summary yaml."""
    yaml_path = os.getenv(
        "PROMPT_PR_BATCH_SUMMARY", str(Path(__file__).parents[0].joinpath(C.PR_BATCH_SUMMARY_PROMPT_YAML))
    )
    return LangChainPrompt.load(yaml_path)


def load_nature_yaml() -> LangChainPrompt:
    """Load the nature yaml."""
    yaml_path = os.getenv("PROMPT_NATURE", str(Path(__file__).parents[0].joinpath(C.PROMPT_NATURE_YAML)))
    return LangChainPrompt.load(yaml_path)
