"""A prompt for the GPT Review task."""
from dataclasses import dataclass

from gpt_review.prompts._prompt import Prompt


@dataclass
class SummaryPrompt(Prompt):
    """A prompt for the GPT summary task."""

    prompt_prefix: str = """Summarize the following file changed in a pull request submitted by a developer on GitHub,
focusing on major modifications, additions, deletions, and any significant updates within the files. Do not include the
file name in the summary and list the summary with bullet points"""
