"""Ask GPT a question."""
import logging
import os
import time
from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup
from knack.util import CLIError

# import constants
import openai

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


from openai.error import RateLimitError

from gpt_review._command import GPTCommandGroup
from gpt_review.constants import (
    MAX_TOKENS_MIN,
    MAX_TOKENS_MAX,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    TOP_P_MIN,
    TOP_P_MAX,
    FREQUENCY_PENALTY_MIN,
    FREQUENCY_PENALTY_MAX,
    PRESENCE_PENALTY_MIN,
    PRESENCE_PENALTY_MAX,
)


DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


def validate_parameter_range(namespace) -> None:
    """Validate that max_tokens is in [1,4000], temperature and top_p are in [0,1], and frequency_penalty and presence_penalty are in [0,2]"""
    _range_validation(namespace.max_tokens, "max-tokens", MAX_TOKENS_MIN, MAX_TOKENS_MAX)
    _range_validation(namespace.temperature, "temperature", TEMPERATURE_MIN, TEMPERATURE_MAX)
    _range_validation(namespace.top_p, "top-p", TOP_P_MIN, TOP_P_MAX)
    _range_validation(namespace.frequency_penalty, "frequency-penalty", FREQUENCY_PENALTY_MIN, FREQUENCY_PENALTY_MAX)
    _range_validation(namespace.presence_penalty, "presence-penalty", PRESENCE_PENALTY_MIN, PRESENCE_PENALTY_MAX)


def _range_validation(param, name, min_value, max_value) -> None:
    """Validates that the given parameter is within the allowed range

    Args:
        param (int or float): The parameter value to validate.
        name (str): The name of the parameter.
        min_value (int or float): The minimum allowed value for the parameter.
        max_value (int or float): The maximum allowed value for the parameter.

    Raises:
        CLIError: If the parameter is not within the allowed range.
    """
    if param is not None and (param < min_value or param > max_value):
        raise CLIError(f"--{name} must be a(n) {type(param).__name__} between {min_value} and {max_value}")


def _ask(question, max_tokens=100, temperature=0.7, top_p=0.5, frequency_penalty=0.5, presence_penalty=0):
    """Ask GPT a question.

    Args:
        question (str): The questin to ask GPT.
        max_tokens (int): The maximum number of tokens to generate.
        temperature (float): This value determines the level of randomness.
        top_p (float): This value also determines the level or randomness.
        frequency_penalty (float): The chance of repeating a token based on current frequency in the text.
        presence_penalty (float): The chance of repeating any token that has appeared in the text so far.

    Yields:
        dict[str, str]: The response from GPT.
    """
    response = _call_gpt(
        prompt=question[0],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )
    return {"response": response}


def _load_azure_openai_context() -> None:
    """
    Load the Azure OpenAI context.

    If the environment variables are not set, retrieve the values from Azure Key Vault.
    """
    openai.api_type = "azure"
    openai.api_version = "2023-03-15-preview"
    if os.getenv("AZURE_OPENAI_API"):
        openai.api_base = os.getenv("AZURE_OPENAI_API")
        openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
    else:
        secret_client = SecretClient(
            vault_url=os.getenv("AZURE_KEY_VAULT_URL", DEFAULT_KEY_VAULT), credential=DefaultAzureCredential()
        )

        openai.api_base = secret_client.get_secret("azure-open-ai").value
        openai.api_key = secret_client.get_secret("azure-openai-key").value


def _call_gpt(
    prompt: str,
    temperature=0.10,
    max_tokens=500,
    top_p=1.0,
    frequency_penalty=0.5,
    presence_penalty=0.0,
    retry=0,
    messages=None,
) -> str:
    """
    Call GPT-4 with the given prompt.

    Args:
        prompt (str): The prompt to send to GPT-4.
        temperature (float, optional): The temperature to use. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 500.
        top_p (float, optional): The top_p to use. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty to use. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty to use. Defaults to 0.0.
        retry (int, optional): The number of times to retry the request. Defaults to 0.

    Returns:
        str: The response from GPT-4.
    """
    _load_azure_openai_context()

    if len(prompt) > 32767:
        return _batch_large_changes(
            prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry, messages
        )

    messages = messages or [{"role": "user", "content": prompt}]
    try:
        engine = _get_engine(prompt)
        logging.info("Model Selected based on prompt size: %s", engine)

        logging.info("Prompt sent to GPT: %s\n", prompt)
        completion = openai.ChatCompletion.create(
            engine=engine,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        return completion.choices[0].message.content  # type: ignore
    except RateLimitError as error:
        if retry < 5:
            logging.warning("Call to GPT failed due to rate limit, retry attempt: %s", retry)
            time.sleep(retry * 5)
            return _call_gpt(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1)
        raise RateLimitError("Retry limit exceeded") from error


def _batch_large_changes(
    prompt: str,
    temperature=0.10,
    max_tokens=500,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.0,
    retry=0,
    messages=None,
) -> str:
    """Placeholder for batching large changes to GPT-4."""
    try:
        logging.warning("Prompt too long, batching")
        output = ""
        for i in range(0, len(prompt), 32767):
            logging.debug("Batching %s to %s", i, i + 32767)
            batch = prompt[i : i + 32767]
            output += _call_gpt(
                batch,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                retry=retry,
                messages=messages,
            )
        prompt = f"""
"Summarize the large file batches"

{output}
"""
        return _call_gpt(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry, messages)
    except RateLimitError:
        logging.warning("Prompt too long, truncating")
        prompt = prompt[:32767]
        return _call_gpt(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            retry=retry,
            messages=messages,
        )


def _get_engine(prompt: str) -> str:
    """
    Get the Engine based on the prompt length.
    - when greater then 8k use gpt-4-32k
    - when greater then 4k use gpt-4
    - use gpt-35-turbo for all small prompts
    """
    if len(prompt) > 8000:
        return "gpt-4-32k"
    return "gpt-4" if len(prompt) > 4000 else "gpt-35-turbo"


class AskCommandGroup(GPTCommandGroup):
    """Ask Command Group."""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        with CommandGroup(loader, "", "gpt_review._ask#{}") as group:
            group.command("ask", "_ask", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader) -> None:
        with ArgumentsContext(loader, "ask") as args:
            args.positional("question", type=str, nargs="+", help="Provide a question to ask GPT.")
            args.argument(
                "temperature",
                type=float,
                help="Sets the level of creativity/randomness.",
                validator=validate_parameter_range,
            )
            args.argument(
                "max_tokens",
                type=int,
                help="The maximum number of tokens to generate.",
                validator=validate_parameter_range,
            )
            args.argument(
                "top_p",
                type=float,
                help="Also sets the level of creativity/randomness. Adjust temperature or top p but not both.",
                validator=validate_parameter_range,
            )
            args.argument(
                "frequency_penalty",
                type=float,
                help="Reduce the chance of repeating a token based on current frequency in the text.",
                validator=validate_parameter_range,
            )
            args.argument(
                "presence_penalty",
                type=float,
                help="Reduce the chance of repeating any token that has appeared in the text so far.",
                validator=validate_parameter_range,
            )
