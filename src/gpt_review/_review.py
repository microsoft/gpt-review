"""Basic functions for requesting review based goals from GPT-4."""
import logging

from gpt_review._ask import _ask


def _request_goal(git_diff, goal) -> str:
    """
    Request a goal from GPT-4.

    Args:
        git_diff (str): The git diff to split.
        goal (str): The goal to request from GPT-4.

    Returns:
        response (str): The response from GPT-4.
    """
    prompt = f"""
{goal}

{git_diff}
"""

    response = _ask(prompt)
    logging.info(response["response"])
    return response["response"]
