"""Open AI API Call Wrapper."""
import logging
import os

import openai
from openai.error import RateLimitError

import gpt_review.constants as C
from gpt_review.context import _load_azure_openai_context
from gpt_review.utils import _retry_with_exponential_backoff


def _count_tokens(prompt) -> int:
    """
    Determine number of tokens in prompt.

    Args:
        prompt (str): The prompt to send to GPT-4.

    Returns:
        int: The number of tokens in the prompt.
    """
    return int(len(prompt) / 4 * 3)


def _get_model(prompt: str, max_tokens: int, fast: bool = False, large: bool = False) -> str:
    """
    Get the OpenAI model based on the prompt length.
    - when greater then 8k use gpt-4-32k
    - otherwise use gpt-4
    - enable fast to use gpt-35-turbo for small prompts

    Args:
        prompt (str): The prompt to send to GPT-4.
        max_tokens (int): The maximum number of tokens to generate.
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.

    Returns:
        str: The model to use.
    """
    context = _load_azure_openai_context()

    tokens = _count_tokens(prompt)
    if large or tokens + max_tokens > 8000:
        return context.large_llm_model_deployment_id
    if tokens + max_tokens > 4000:
        return context.smart_llm_model_deployment_id
    return context.turbo_llm_model_deployment_id if fast else context.smart_llm_model_deployment_id


def _call_gpt(
    prompt: str,
    temperature=0.10,
    max_tokens=500,
    top_p=1.0,
    frequency_penalty=0.5,
    presence_penalty=0.0,
    retry=0,
    messages=None,
    fast: bool = False,
    large: bool = False,
) -> str:
    """
    Call GPT with the given prompt.

    Args:
        prompt (str): The prompt to send to GPT-4.
        temperature (float, optional): The temperature to use. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 500.
        top_p (float, optional): The top_p to use. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty to use. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty to use. Defaults to 0.0.
        retry (int, optional): The number of times to retry the request. Defaults to 0.
        messages (List[Dict[str, str]], optional): The messages to send to GPT-4. Defaults to None.
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.

    Returns:
        str: The response from GPT.
    """
    messages = messages or [{"role": "user", "content": prompt}]
    logging.debug("Prompt sent to GPT: %s\n", prompt)

    try:
        model = _get_model(prompt, max_tokens=max_tokens, fast=fast, large=large)
        logging.debug("Model Selected based on prompt size: %s", model)

        if os.environ.get("OPENAI_API_TYPE", "") == C.AZURE_API_TYPE:
            logging.debug("Using Azure Open AI.")
            completion = openai.ChatCompletion.create(
                deployment_id=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
        else:
            logging.debug("Using Open AI.")
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
        return completion.choices[0].message.content  # type: ignore
    except RateLimitError as error:
        if retry < C.MAX_RETRIES:
            retry_after = error.headers.get("Retry-After", C.DEFAULT_RETRY_AFTER)
            _retry_with_exponential_backoff(retry, retry_after)

            return _call_gpt(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1)
        raise RateLimitError("Retry limit exceeded") from error
