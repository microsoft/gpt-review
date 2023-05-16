"""Wrapper for Llama Index."""
import logging
import os
from typing import List, Optional

import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import AzureOpenAI
from llama_index import (
    Document,
    GithubRepositoryReader,
    GPTVectorStoreIndex,
    LangchainEmbedding,
    LLMPredictor,
    ServiceContext,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.indices.base import BaseGPTIndex
from llama_index.storage.storage_context import DEFAULT_PERSIST_DIR
from typing_extensions import override

import gpt_review.constants as C
from gpt_review.context import _load_azure_openai_context

logger = logging.getLogger(__name__)


def _query_index(
    question: str,
    files: Optional[List[str]] = None,
    input_dir: Optional[str] = None,
    exclude_hidden: bool = True,
    recursive: bool = True,
    required_exts: Optional[List[str]] = None,
    repository: Optional[str] = None,
    branch: str = "main",
    fast: bool = False,
    large: bool = False,
    reset: bool = False,
) -> str:
    """
    Query a Vector Index with GPT.
    Args:
        question (List[str]): The question to ask.
        files (List[str], optional): The files to search.
            (Optional; overrides input_dir, exclude)
        input_dir (str, optional): Path to the directory.
        exclude_hidden (bool): Whether to exclude hidden files.
        recursive (bool): Whether to search directory recursively.
        required_exts (List, optional): The required extensions for files in directory.
        repository (str): The repository to search. Format: owner/repo
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.
        reset (bool, optional): Whether to reset the index. Defaults to False.

    Returns:
        Dict[str, str]: The response.
    """
    documents = []
    if files:
        documents += SimpleDirectoryReader(input_files=files).load_data()
    elif input_dir:
        documents += SimpleDirectoryReader(
            input_dir=input_dir, exclude_hidden=exclude_hidden, recursive=recursive, required_exts=required_exts
        ).load_data()
    if repository:
        owner, repo = repository.split("/")
        documents += GithubRepositoryReader(owner=owner, repo=repo, use_parser=False).load_data(branch=branch)

    index = _load_index(documents, fast=fast, large=large, reset=reset)

    return index.as_query_engine().query(question).response  # type: ignore


def _load_index(
    documents: List[Document],
    fast: bool = True,
    large: bool = True,
    reset: bool = False,
    persist_dir: str = DEFAULT_PERSIST_DIR,
) -> BaseGPTIndex:
    """
    Load or create a document indexer.

    Args:
        documents (List[Document]): The documents to index.
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.
        reset (bool, optional): Whether to reset the index. Defaults to False.
        persist_dir (str, optional): The directory to persist the index to. Defaults to './storage'.

    Returns:
        BaseGPTIndex: The document indexer.
    """
    service_context = _load_service_context(fast, large)

    if os.path.isdir(f"{persist_dir}") and not reset:
        logger.info("Loading index from storage")
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(service_context=service_context, storage_context=storage_context)

    logger.info("Creating index")
    index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)

    logger.info("Saving index to storage")
    index.storage_context.persist(persist_dir=persist_dir)

    return index


def _load_service_context(fast: bool = False, large: bool = False) -> ServiceContext:
    """
    Load the service context.

    Args:
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.

    Returns:
        ServiceContext: The service context.
    """

    context = _load_azure_openai_context()
    model_name = (
        context.turbo_llm_model_deployment_id
        if fast
        else context.large_llm_model_deployment_id
        if large
        else context.smart_llm_model_deployment_id
    )

    if openai.api_type == C.AZURE_API_TYPE:
        llm_type = AzureGPT35Turbo if fast else AzureChatOpenAI
        llm = llm_type(  # type: ignore
            deployment_name=model_name,
            model_kwargs={
                "api_key": openai.api_key,
                "api_base": openai.api_base,
                "api_type": openai.api_type,
                "api_version": openai.api_version,
            },
            max_retries=C.MAX_RETRIES,
        )
    else:
        llm = ChatOpenAI(
            model_name=model_name,
            model_kwargs={
                "api_key": openai.api_key,
                "api_base": openai.api_base,
                "api_type": openai.api_type,
                "api_version": openai.api_version,
            },
            max_retries=C.MAX_RETRIES,
        )

    llm_predictor = LLMPredictor(llm=llm)

    embedding_llm = LangchainEmbedding(
        OpenAIEmbeddings(
            model="text-embedding-ada-002",
        ),  # type: ignore
        embed_batch_size=1,
    )

    return ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=embedding_llm,
    )


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
