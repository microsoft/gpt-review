"""Prompt for PR summarization."""
import os
from pathlib import Path
from gpt_review.prompts._prompt import LangChainPrompt
import gpt_review.constants as C


def load_pr_summary_yaml() -> LangChainPrompt:
    """Load the summary yaml."""
    yaml_path = os.getenv("PROMPT_PR_SUMMARY", str(Path(__file__).parents[0].joinpath(C.PR_SUMMARY_PROMPT_YAML)))
    return LangChainPrompt.load(yaml_path)
