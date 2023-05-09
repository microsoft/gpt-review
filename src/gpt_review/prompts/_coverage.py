"""A prompt for the GPT Coverage task."""
from gpt_review.prompts._prompt import Prompt


class CoveragePrompt(Prompt):
    """A prompt for the GPT Coverage task."""

    prompt_prefix: str = """You are an experienced software developer. Generate unit test cases for the code submitted
in the pull request, ensuring comprehensive coverage of all functions, methods, and scenarios to validate the
correctness and reliability of the implementation."""
