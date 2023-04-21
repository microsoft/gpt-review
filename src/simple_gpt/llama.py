import os

from typing import List

import yaml


from llama_index.response.schema import RESPONSE_TYPE
from llama_index import (
    Document,
    GPTSimpleVectorIndex,
    SimpleDirectoryReader,
    GithubRepositoryReader,
    LangchainEmbedding,
    PromptHelper,
    ServiceContext,
    LLMPredictor,
)

import openai
from langchain.llms import AzureOpenAI
from langchain.embeddings import OpenAIEmbeddings

from simple_gpt.report import _load_azure_openai_context


def llamma_question(dir_name: str, query: str, index_path="index.json") -> RESPONSE_TYPE:
    """
    Ask a question of a directory of code.

    Args:
        dir_name (str): The directory to ask the question of.
        query (str): The question to ask.
        index_path (str): The path to the index.

    Returns:
        RESPONSE_TYPE: The response from the Llama Index.
    """
    documents = SimpleDirectoryReader(dir_name).load_data()
    index = _load_llama_index(index_path, documents)

    return index.query(query)


def detect_programming_language(dir_name: str, index_path="index.json"):
    """
    Detect the programming language of a directory of code.

    Args:
        dir_name (str): The directory to detect the programming language of.

    Returns:
        List[str]: The programming languages detected.
    """
    question = """What programming langauge is this code written in?
Here is an example response, format the response as a list of languages:
```yaml
languages:
- language1
```
"""
    response = llamma_question(dir_name, question, index_path).response

    yaml_response = yaml.safe_load(response)
    return yaml_response["languages"]


def _load_llama_index(index_path: str, documents: List[Document], reuse=False):
    """Check if index.json exists and load_from_disk, otherwise create from_documents"""
    if reuse and os.path.exists(index_path):
        return GPTSimpleVectorIndex.load_from_disk(index_path)
    index = document_indexer(documents)
    # index = GPTSimpleVectorIndex.from_documents(documents)
    index.save_to_disk(index_path)
    return index


def repo_question(question, owner, repo, branch="main", github_token=None, index_path="index.json"):
    """
    Ask a question of a directory of code.

    Args:
        question (str): The question to ask.
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        branch (str): The branch of the repository.
        github_token (str): The GitHub token to use.

    Returns:
        RESPONSE_TYPE: The response from the Llama Index.
    """
    github_token = github_token or os.environ.get("PAT") or os.environ.get("GITHUB_TOKEN")

    documents = GithubRepositoryReader(
        github_token=github_token,
        owner=owner,
        repo=repo,
        use_parser=False,
        verbose=False,
    ).load_data(branch=branch)
    index = document_indexer(documents)
    index.save_to_disk(index_path)
    return index.query(question, verbose=True)


def document_indexer(documents):
    """
    Create a document indexer.

    Args:
        documents (List[Document]): The documents to index.
        azure (bool): Whether to use Azure OpenAI.

    Returns:
        GPTSimpleVectorIndex: The document indexer.
    """
    if os.getenv("AZURE_OPENAI_API_KEY"):
        _load_azure_openai_context()

        os.environ["OPENAI_API_KEY"] = openai.api_key
        llm = AzureOpenAI(
            deployment_name="text-davinci-003",
            model_kwargs={
                "api_key": openai.api_key,
                "api_base": openai.api_base,
                "api_type": "azure",
                "api_version": "2023-03-15-preview",
            },
            max_retries=10,
        )  # type: ignore
        llm_predictor = LLMPredictor(llm=llm)

        embedding_llm = LangchainEmbedding(
            OpenAIEmbeddings(
                document_model_name="text-embedding-ada-002",
                query_model_name="text-embedding-ada-002",
            ),  # type: ignore
            embed_batch_size=1,
        )

        prompt_helper = PromptHelper(max_input_size=500, num_output=1, max_chunk_overlap=20)
        service_context = ServiceContext.from_defaults(
            llm_predictor=llm_predictor,
            embed_model=embedding_llm,
            prompt_helper=prompt_helper,
        )
        return GPTSimpleVectorIndex.from_documents(documents, service_context=service_context)
    return GPTSimpleVectorIndex.from_documents(documents)


def detect_repo_language(owner, repo, branch="main", github_token=None, index_path="index.json"):
    """
    Detect the programming language of a directory of code.

    Args:
        dir_name (str): The directory to detect the programming language of.

    Returns:
        List[str]: The programming languages detected.
    """
    question = """What programming langauge is this code written in?
Here is an example response, format the response as a list of languages:
```yaml
languages:
- language1
```
"""
    response = repo_question(question, owner, repo, branch, github_token, index_path).response

    yaml_response = yaml.safe_load(response)
    return yaml_response["languages"]
