"""Context for the Azure OpenAI API and the models."""
import os
from dataclasses import dataclass

import openai
import yaml
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

import gpt_review.constants as C


@dataclass
class Context:
    azure_api_base: str
    azure_api_type: str = C.AZURE_API_TYPE
    azure_api_version: str = C.AZURE_API_VERSION
    turbo_llm_model_deployment_id: str = C.AZURE_TURBO_MODEL
    smart_llm_model_deployment_id: str = C.AZURE_SMART_MODEL
    large_llm_model_deployment_id: str = C.AZURE_LARGE_MODEL
    embedding_model_deployment_id: str = C.AZURE_EMBEDDING_MODEL


def _load_context_file():
    """Import from yaml file and return the context."""
    context_file = os.getenv("CONTEXT_FILE", C.AZURE_CONFIG_FILE)
    with open(context_file, "r", encoding="utf8") as file:
        return yaml.load(file, Loader=yaml.SafeLoader)


def _load_azure_openai_context() -> Context:
    """Load the context from the environment variables or the context file.

    If a config file is available its values will take precedence. Otherwise
    it will first check for an AZURE_OPENAI_API key, next OPENAI_API_KEY, and
    lastly the Azure Key Vault.

    Returns:
        Context: The context for the Azure OpenAI API and the models.
    """
    azure_config = _load_context_file() if os.path.exists(os.getenv("CONTEXT_FILE", C.AZURE_CONFIG_FILE)) else {}

    if azure_config.get("azure_api_type"):
        openai.api_type = os.environ["OPENAI_API_TYPE"] = azure_config.get("azure_api_type")
    elif os.getenv("AZURE_OPENAI_API"):
        openai.api_type = os.environ["OPENAI_API_TYPE"] = C.AZURE_API_TYPE
    elif "OPENAI_API_TYPE" in os.environ:
        openai.api_type = os.environ["OPENAI_API_TYPE"]

    if azure_config.get("azure_api_version"):
        openai.api_version = os.environ["OPENAI_API_VERSION"] = azure_config.get("azure_api_version")
    elif os.getenv("AZURE_OPENAI_API"):
        openai.api_version = os.environ["OPENAI_API_VERSION"] = C.AZURE_API_VERSION
    elif "OPENAI_API_VERSION" in os.environ:
        openai.api_version = os.environ["OPENAI_API_VERSION"]

    if os.getenv("AZURE_OPENAI_API"):
        openai.api_type = os.environ["OPENAI_API_TYPE"] = C.AZURE_API_TYPE
        openai.api_base = os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_API") or azure_config.get(
            "azure_api_base"
        )
        openai.api_key = os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")  # type: ignore
    elif os.getenv("OPENAI_API_KEY"):
        openai.api_key = os.environ["OPENAI_API_KEY"]
    else:
        kv_client = SecretClient(
            vault_url=os.getenv("AZURE_KEY_VAULT_URL", C.AZURE_KEY_VAULT),
            credential=DefaultAzureCredential(additionally_allowed_tenants=["*"]),
        )
        openai.api_type = os.environ["OPENAI_API_TYPE"] = C.AZURE_API_TYPE
        openai.api_base = os.environ["OPENAI_API_BASE"] = kv_client.get_secret("azure-open-ai").value  # type: ignore
        openai.api_key = os.environ["OPENAI_API_KEY"] = kv_client.get_secret("azure-openai-key").value  # type: ignore

    return Context(
        azure_api_base=openai.api_base,
        azure_api_type=openai.api_type,
        azure_api_version=openai.api_version,
        **azure_config.get("azure_model_map", {}),
    )
