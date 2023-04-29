"""Ask GPT a question."""
import logging
import os
import time
from typing import Dict, List
from typing_extensions import override
from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup
from knack.util import CLIError

import openai
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai.error import RateLimitError
from langchain.llms import AzureOpenAI
from langchain.embeddings import OpenAIEmbeddings
from llama_index import (
    GPTSimpleVectorIndex,
    LangchainEmbedding,
    ServiceContext,
    LLMPredictor,
    SimpleDirectoryReader,
)
from llama_index.indices.base import BaseGPTIndex

from gpt_review._command import GPTCommandGroup
import gpt_review.constants as C


DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


def _ask_doc(question: List[str], files: List[str]) -> str:
    """
    Ask GPT a question.

    Args:
        question (List[str]): The question to ask.
        files (List[str]): The files to search.

    Returns:
        Dict[str, str]: The response.
    """
    documents = SimpleDirectoryReader(input_files=files).load_data()
    index = _document_indexer(documents)

    return index.query(" ".join(question)).response  # type: ignore


def _document_indexer(documents) -> BaseGPTIndex:
    """
    Create a document indexer.

    Deployment names include: "gpt-35-turbo", "text-davinci-003"

    Args:
        documents (List[Document]): The documents to index.
        azure (bool): Whether to use Azure OpenAI.

    Returns:
        GPTSimpleVectorIndex: The document indexer.
    """
    _load_azure_openai_context()

    llm = AzureGPT35Turbo(  # type: ignore
        deployment_name="gpt-35-turbo",
        model_kwargs={
            "api_key": openai.api_key,
            "api_base": openai.api_base,
            "api_type": "azure",
            "api_version": "2023-03-15-preview",
        },
        max_retries=10,
    )
    llm_predictor = LLMPredictor(llm=llm)

    embedding_llm = LangchainEmbedding(
        OpenAIEmbeddings(
            document_model_name="text-embedding-ada-002",
            query_model_name="text-embedding-ada-002",
        ),  # type: ignore
        embed_batch_size=1,
    )

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=embedding_llm,
    )
    return GPTSimpleVectorIndex.from_documents(documents, service_context=service_context)


class AzureGPT35Turbo(AzureOpenAI):
    """Azure OpenAI Chat API."""

    @property
    @override
    def _default_params(self):
        """
        Get the default parameters for calling OpenAI API.
        gpt-35-turbo does not support best_of, logprobs, or echo.
        """
        normal_params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "n": self.n,
            "request_timeout": self.request_timeout,
            "logit_bias": self.logit_bias,
        }
        return {**normal_params, **self.model_kwargs}


def validate_parameter_range(namespace) -> None:
    """Validate that max_tokens is in [1,4000], temperature and top_p are in [0,1], and frequency_penalty and presence_penalty are in [0,2]"""
    _range_validation(namespace.max_tokens, "max-tokens", C.MAX_TOKENS_MIN, C.MAX_TOKENS_MAX)
    _range_validation(namespace.temperature, "temperature", C.TEMPERATURE_MIN, C.TEMPERATURE_MAX)
    _range_validation(namespace.top_p, "top-p", C.TOP_P_MIN, C.TOP_P_MAX)
    _range_validation(
        namespace.frequency_penalty, "frequency-penalty", C.FREQUENCY_PENALTY_MIN, C.FREQUENCY_PENALTY_MAX
    )
    _range_validation(namespace.presence_penalty, "presence-penalty", C.PRESENCE_PENALTY_MIN, C.PRESENCE_PENALTY_MAX)


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


def _ask(
    question,
    max_tokens=C.MAX_TOKENS_DEFAULT,
    temperature=C.TEMPERATURE_DEFAULT,
    top_p=C.TOP_P_DEFAULT,
    frequency_penalty=C.FREQUENCY_PENALTY_DEFAULT,
    presence_penalty=C.PRESENCE_PENALTY_DEFAULT,
    files=None,
) -> Dict[str, str]:
    """Ask GPT a question.

    Args:
        question (str): The questin to ask GPT.
        max_tokens (int): The maximum number of tokens to generate.
        temperature (float): This value determines the level of randomness.
        top_p (float): This value also determines the level or randomness.
        frequency_penalty (float): The chance of repeating a token based on current frequency in the text.
        presence_penalty (float): The chance of repeating any token that has appeared in the text so far.
        files (List[str]): The files to search.

    Yields:
        dict[str, str]: The response from GPT.
    """
    if files:
        response = _ask_doc(question, files)
    else:
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

    Set both the environment variables and the openai package variables.
    - Without setting the environment variables, the integration tests fail.
    - Without setting the openai package variables, the cli tests fail.
    """
    openai.api_type = "azure"
    openai.api_version = "2023-03-15-preview"

    if os.getenv("AZURE_OPENAI_API"):
        openai.api_base = os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API")  # type: ignore
        openai.api_key = os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")  # type: ignore
    else:
        kv_client = SecretClient(
            vault_url=os.getenv("AZURE_KEY_VAULT_URL", DEFAULT_KEY_VAULT), credential=DefaultAzureCredential()
        )
        openai.api_base = os.environ["OPENAI_API_BASE"] = kv_client.get_secret("azure-open-ai").value  # type: ignore
        openai.api_key = os.environ["OPENAI_API_KEY"] = kv_client.get_secret("azure-openai-key").value  # type: ignore


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
            args.argument(
                "files",
                type=str,
                help="Ask question about a file. Can be used multiple times.",
                default=None,
                action="append",
            )
