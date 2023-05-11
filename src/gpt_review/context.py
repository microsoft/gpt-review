"""Context for the Azure OpenAI API and the models."""
import os
from dataclasses import dataclass
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import openai
import yaml

import gpt_review.constants as C

DEFAULT_KEY_VAULT = "https://dciborow-openai.vault.azure.net/"


@dataclass
class Context:
    azure_api_base: str
    azure_api_type: str = "azure"
    azure_api_version: str = "2023-03-15-preview"
    turbo_llm_model_deployment_id: str = "gpt-35-turbo"
    smart_llm_model_deployment_id: str = "gpt-4"
    large_llm_model_deployment_id: str = "gpt-4-32k"
    embedding_model_deployment_id: str = "text-embedding-ada-002"


def load_context_file():
    """Import from yaml file and return the context."""
    context_file = os.getenv("CONTEXT_FILE", "azure.yaml")
    with open(context_file, "r", encoding="utf8") as file:
        return yaml.load(file, Loader=yaml.SafeLoader)


def _load_azure_openai_context() -> Context:
    """
    Load the Azure OpenAI context.
    If the environment variables are not set, retrieve the values from Azure Key Vault.
    Set both the environment variables and the openai package variables.
    - Without setting the environment variables, the integration tests fail.
    - Without setting the openai package variables, the cli tests fail.
    """

    azure_config = load_context_file() if os.path.exists(os.getenv("CONTEXT_FILE", C.AZURE_CONFIG_FILE)) else {}

    openai.api_type = os.environ["OPENAI_API_TYPE"] = azure_config.get("azure_api_type", C.AZURE_API_TYPE)
    openai.api_version = os.environ["OPENAI_API_VERSION"] = azure_config.get("azure_api_version", C.AZURE_API_VERSION)

    if os.getenv("AZURE_OPENAI_API"):
        openai.api_base = os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API") or azure_config.get(
            "azure_api_base"
        )
        openai.api_key = os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")  # type: ignore
    else:  # pragma: no cover
        kv_client = SecretClient(
            vault_url=os.getenv("AZURE_KEY_VAULT_URL", DEFAULT_KEY_VAULT), credential=DefaultAzureCredential()
        )
        openai.api_base = os.environ["OPENAI_API_BASE"] = kv_client.get_secret("azure-open-ai").value  # type: ignore
        openai.api_key = os.environ["OPENAI_API_KEY"] = kv_client.get_secret("azure-openai-key").value  # type: ignore

    return Context(
        azure_api_base=openai.api_base,
        azure_api_type=openai.api_type,
        azure_api_version=openai.api_version,
        **azure_config.get("azure_model_map", {}),
    )
