
from langchain_ollama import ChatOllama

from app.core.config import settings


def get_llm(temperature: float | None = None) -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        num_ctx=settings.ollama_num_ctx,
        num_predict=settings.ollama_num_predict,
        temperature=(
            settings.ollama_temperature
            if temperature is None
            else temperature
        ),
        keep_alive="0s",
        client_kwargs={
            "timeout": settings.ollama_timeout,
        },
    )
