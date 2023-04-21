"""Generate Summary Report with GPT"""
import logging
import os
import time
import openai
import yaml

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


from openai.error import RateLimitError, InvalidRequestError

DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


def process_yaml(git_diff, yaml_file, headers=True):
    """Process a yaml file.

    Args:
        git_diff (str): The diff of the PR.
        yaml_file (str): The path to the yaml file.

    Returns:
        str: The report.
    """
    config = yaml.safe_load(yaml_file)
    report = config["report"]
    return process_report(git_diff, report, headers=headers)


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
            logging.debug(f"Batching {i} to {i+32767}")
            batch = prompt[i : i + 32767]
            output += call_gpt4(
                batch,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                retry=retry,
                messages=messages,
            )

        return request_goal(output, "Summarize the large file batches")
    except RateLimitError:
        logging.warning("Prompt too long, truncating")
        prompt = prompt[:32767]
        return call_gpt4(
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


def call_gpt4(
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
    if len(prompt) > 32767:
        logging.warning("Prompt too long, truncating")
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
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        return completion.choices[0].message.content
    except InvalidRequestError:
        return call_gpt4(prompt[:32767], temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1)
    except RateLimitError as error:
        if retry < 5:
            time.sleep(retry * 5)
            return call_gpt4(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, retry + 1)
        raise RateLimitError("Retry limit exceeded") from error


def call_gpt(
    prompt: str = "",
    temperature=0.10,
    max_tokens=500,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0.0,
    messages=None,
) -> str:
    """Call GPT-3 or GPT-4 depending on the model.

    Args:
        prompt (str): The prompt to send to GPT-3 or GPT-4.
        temperature (float, optional): The temperature to use. Defaults to 0.10.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 500.
        top_p (float, optional): The top_p to use. Defaults to 1.
        frequency_penalty (float, optional): The frequency penalty to use. Defaults to 0.5.
        presence_penalty (float, optional): The presence penalty to use. Defaults to 0.0.

    Returns:
        str: The response from GPT-3 or GPT-4.
    """
    _load_azure_openai_context()

    return call_gpt4(prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, messages=messages)


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


def request_goal(git_diff, goal=None, max_tokens=500) -> str:
    """
    Request a goal from GPT-4.

    Args:
        git_diff (str): The git diff to split.
        goal (str): The goal to request from GPT-4.

    Returns:
        response (str): The response from GPT-4.
    """
    goal = goal or ""
    prompt = f"""
{goal}

{git_diff}
"""

    response = call_gpt(prompt, max_tokens=max_tokens)
    logging.info(response)
    return response


def process_report(git_diff, report: dict, indent="#", headers=True) -> str:
    """
    for-each record in report
    - if record is a string, check_goals
    - else recursively call process_report
    """
    text = ""
    for key, record in report.items():
        if isinstance(record, str) or record is None:
            if headers:
                header = key if key != "_" else ""
                text += f"""
{indent} {header}

"""
            text += f"{request_goal(git_diff, goal=record)}"

        else:
            text += f"""
{indent} {key}

"""
            text += process_report(git_diff, record, indent=f"{indent}#", headers=headers)

    return text
