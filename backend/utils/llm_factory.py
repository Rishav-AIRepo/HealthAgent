from langchain_openai import AzureChatOpenAI
from config.settings import get_settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_llm() -> AzureChatOpenAI:
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment_name,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        temperature=0.3,
        max_tokens=2000,
    )
