from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import os
from settings import settings

embed_model = AzureOpenAIEmbeddings(
    azure_deployment=settings.azure_embbeding_model,
    openai_api_key=settings.azure_api_key,
    azure_endpoint=settings.azure_endpoint,
    api_version=settings.azure_api_version,
)

llm = AzureChatOpenAI(
    temperature=0,
    model="gpt-4o",
    azure_deployment="gpt-4o",
    openai_api_key=settings.azure_api_key,
    azure_endpoint=settings.azure_endpoint,
    api_version=settings.azure_api_version,
)

llm_gpt4omini = AzureChatOpenAI(
    temperature=0,
    model="gpt-4o-mini",
    azure_deployment="gpt-4o-mini",
    openai_api_key=settings.azure_api_key,
    azure_endpoint=settings.azure_endpoint,
    api_version=settings.azure_api_version,
)


llm_gpt41mini = AzureChatOpenAI(
    temperature=0,
    model="gpt-4.1-mini",
    azure_deployment="gpt-4.1-mini",
    openai_api_key=settings.azure_api_key,
    azure_endpoint=settings.azure_endpoint,
    api_version=settings.azure_api_version,
)
