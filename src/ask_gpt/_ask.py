"""Ask GPT a question."""
import logging
import os
import time
from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup

import openai

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


from openai.error import RateLimitError


from ask_gpt._command import GPTCommandGroup

DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


def _ask(question, max_tokens=100):
    """Ask GPT a question."""
    response = _call_gpt(prompt=question[0], max_tokens=max_tokens)
    return {"response": response}


def _load_azure_openai_context():
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
    top_p=1,
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
    def load_command_table(loader: CLICommandsLoader):
        with CommandGroup(loader, "", "ask_gpt._ask#{}") as group:
            group.command("ask", "_ask", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader):
        with ArgumentsContext(loader, "ask") as args:
            args.positional("question", type=str, nargs="+", help="Provide a question to ask GPT.")
            args.argument("max_tokens", type=int, help="The maximum number of tokens to generate.")
