"""A prompt for the GPT Suggestion task."""
from gpt_review.prompts.prompt import Prompt


class SuggestionsPrompt(Prompt):
    """A prompt for the GPT Suggestion task."""
    prompt_suffix: str = "provide a list of suggestions of the code"
