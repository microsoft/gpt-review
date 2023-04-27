"""Ask GPT a question."""
import logging
import os
import time
from typing_extensions import override
from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup

import openai
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai.error import RateLimitError
from langchain.chains.conversation.memory import ConversationBufferMemory
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
from llama_index.langchain_helpers.agents import (
    LlamaToolkit,
    create_llama_chat_agent,
    IndexToolConfig,
)

from gpt_review._command import GPTCommandGroup

DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


def _ask(question, files=None, max_tokens=100) -> dict:
    """
    Ask GPT a question.

    Args:
        question (str): The question to ask.
        files (List[str]): The files to search.
        max_tokens (int): The maximum number of tokens to use.

    Returns:
        Dict[str, str]: The response.
    """

    question = " ".join(question)

    if isinstance(files, str):
        files = [files]

    if files:
        response = _ask_doc(question, files)
    else:
        response = _request_goal(question, max_tokens)
    return {"response": response}


def _ask_doc(question, files) -> str:
    """
    Ask GPT a question.

    Args:
        question (str): The question to ask.
        files (List[str]): The files to search.

    Returns:
        Dict[str, str]: The response.
    """
    documents = SimpleDirectoryReader(input_files=files).load_data()
    index = _document_indexer(documents)

    return index.query(question).response  # type: ignore


def _document_indexer(documents) -> BaseGPTIndex:
    """
    Create a document indexer.

    Args:
        documents (List[Document]): The documents to index.
        azure (bool): Whether to use Azure OpenAI.

    Returns:
        GPTSimpleVectorIndex: The document indexer.
    """
    service_context = None
    if os.getenv("AZURE_OPENAI_API_KEY"):
        _load_azure_openai_context()

        os.environ["OPENAI_API_KEY"] = openai.api_key  # type: ignore
        llm = AzureGPT35Turbo(  # type: ignore
            deployment_name="gpt-35-turbo",  # "gpt-35-turbo", # "text-davinci-003",
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


def _llama_agent_chain(index, question):
    """
    Ask GPT a question using llama_index.

    Args:
        index (str): The index to use.
        question (str): The question to ask.

    Returns:
        Dict[str, str]: The response.
    """
    # Load indices from disk
    _load_azure_openai_context()

    os.environ["OPENAI_API_KEY"] = openai.api_key  # type: ignore
    index_set = {"doc": index}

    index_configs = []
    for doc in ["doc"]:
        tool_config = IndexToolConfig(
            index=index_set[doc],
            name=f"Vector Index {doc}",
            description=f"Document to use to answer questions {doc}",
            index_query_kwargs={"similarity_top_k": 3},
            tool_kwargs={"return_direct": True, "return_sources": True},
        )
        index_configs.append(tool_config)

    toolkit = LlamaToolkit(index_configs=index_configs)
    memory = ConversationBufferMemory(memory_key="chat_history")
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

    agent_chain = create_llama_chat_agent(toolkit, llm, memory=memory, verbose=True)
    return agent_chain.run(input=str(question))


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


def _request_goal(git_diff, goal=None, max_tokens=500) -> str:
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

    response = _call_gpt(prompt, max_tokens=max_tokens)
    logging.info(response)
    return response


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
            vault_url=os.getenv("AZURE_KEY_VAULT_URL", DEFAULT_KEY_VAULT),
            credential=DefaultAzureCredential(),
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
            prompt,
            temperature,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
            retry,
            messages,
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
            return _call_gpt(
                prompt,
                temperature,
                max_tokens,
                top_p,
                frequency_penalty,
                presence_penalty,
                retry + 1,
            )
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
    output = ""

    try:
        logging.warning("Prompt too long, batching")

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

        return _request_goal(output, "Summarize the large file batches")
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
                "files",
                type=str,
                help="Ask question about a file. Can be used multiple times.",
                default=None,
                action='append',
            )
            args.argument("max_tokens", type=int, help="The maximum number of tokens to generate.")
