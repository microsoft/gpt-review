"""Wrapper for Llama Index."""
from typing import List, Optional
from typing_extensions import override
import openai

from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import AzureOpenAI
from llama_index import (
    Document,
    GPTVectorStoreIndex,
    LLMPredictor,
    LangchainEmbedding,
    ServiceContext,
    SimpleDirectoryReader,
    GithubRepositoryReader,
)
from llama_index.indices.base import BaseGPTIndex


def _ask_doc(
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
) -> str:
    """
    Ask GPT a question.
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

    # index = _load_index(documents, fast, large)
    index = _document_indexer(documents, fast=fast, large=large)

    return index.as_query_engine().query(question).response  # type: ignore


def _load_index(documents, fast, large, save=True) -> BaseGPTIndex:
    documents_hash = hash(tuple(documents))
    # Load File based on docuemnts_hash
    with open(f".index/{documents_hash}.json", "r") as f:
        index = f.read()
        return BaseGPTIndex.load(index)
    index = _document_indexer(documents, fast=fast, large=large)
    if save:
        index.save(f".index/{documents_hash}.json")
    return index


def _document_indexer(
    documents: List[Document],
    fast: bool = False,
    large: bool = False,
) -> BaseGPTIndex:
    """
    Create a document indexer.
    Deployment names include: "gpt-4", "gpt-4-32", "gpt-35-turbo", "text-davinci-003"
    Args:
        documents (List[Document]): The documents to index.
        fast (bool, optional): Whether to use the fast model. Defaults to False.
        large (bool, optional): Whether to use the large model. Defaults to False.

    Returns:
        GPTVectorStoreIndex: The document indexer.
    """
    llm_type = AzureGPT35Turbo if fast else AzureChatOpenAI
    llm_name = "gpt-35-turbo" if fast else "gpt-4-32k" if large else "gpt-4"
    llm = llm_type(  # type: ignore
        deployment_name=llm_name,
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
            model="text-embedding-ada-002",
        ),  # type: ignore
        embed_batch_size=1,
    )

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=embedding_llm,
    )
    return GPTVectorStoreIndex.from_documents(documents, service_context=service_context)


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
