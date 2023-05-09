"""A prompt for the GPT Review task."""
from gpt_review.prompts.prompt import Prompt


class ReviewPrompt(Prompt):
    """A prompt for the GPT review task."""

    prompt_prefix: str = """Summarize the following file changed in a pull request submitted by a developer on GitHub,
focusing on major modifications, additions, deletions, and any significant updates within the files. Do not include the
file name in the summary and list the summary with bullet points"""
