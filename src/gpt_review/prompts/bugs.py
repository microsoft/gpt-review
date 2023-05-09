"""A prompt for the GPT Bug Review task."""
from gpt_review.prompts.prompt import Prompt


class BugPrompt(Prompt):
    """A prompt for the GPT Review task."""

    prompt_prefix: str = """Provide a concise summary of the bug found in the code, describing its characteristics,
location, and potential effects on the overall functionality and performance of the application. Present the potential
issues and errors first, following by the most important findings, in your summary"""