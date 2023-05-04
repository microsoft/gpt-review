"""Wrapper for Llama Index."""
from typing import List
from typing_extensions import override
import openai

from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import AzureOpenAI
from llama_index import GPTVectorStoreIndex, LLMPredictor, LangchainEmbedding, ServiceContext, SimpleDirectoryReader
from llama_index.indices.base import BaseGPTIndex


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


def _document_indexer(
    documents,
    fast: bool = False,
) -> BaseGPTIndex:
    """
    Create a document indexer.
    Deployment names include: "gpt-35-turbo", "text-davinci-003"
    Args:
        documents (List[Document]): The documents to index.
        azure (bool): Whether to use Azure OpenAI.
    Returns:
        GPTVectorStoreIndex: The document indexer.
    """
    llmType = AzureGPT35Turbo if fast else AzureChatOpenAI
    llm = llmType(  # type: ignore
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
            model="text-embedding-ada-002",
        ),  # type: ignore
        embed_batch_size=1,
    )

    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor,
        embed_model=embedding_llm,
    )
    return GPTVectorStoreIndex.from_documents(documents, service_context=service_context)


def _ask_doc(question: str, files: List[str], fast: bool = False) -> str:
    """
    Ask GPT a question.
    Args:
        question (List[str]): The question to ask.
        files (List[str]): The files to search.
    Returns:
        Dict[str, str]: The response.
    """
    documents = SimpleDirectoryReader(input_files=files).load_data()
    index = _document_indexer(documents, fast=fast)

    return index.as_query_engine().query(question).response  # type: ignore
