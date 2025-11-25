"""Lightweight LangChain chat model wrapper with provider switching."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Iterable, Mapping

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for building chat models."""

    provider: LLMProvider = LLMProvider.OLLAMA
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None
    base_url: str | None = "http://127.0.0.1:11434"  # Used by Ollama

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.getenv("LLM_PROVIDER", LLMProvider.OLLAMA.value)
        model = os.getenv("LLM_MODEL")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        max_tokens_env = os.getenv("LLM_MAX_TOKENS")
        max_tokens = int(max_tokens_env) if max_tokens_env else None
        base_url = os.getenv("OLLAMA_BASE_URL")

        return cls(
            provider=LLMProvider(provider),
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url=base_url,
        )

    def with_updates(self, **overrides: Any) -> "LLMConfig":
        return replace(self, **overrides)


class BaseModel:
    """Minimal wrapper around LangChain chat models with provider switching."""

    def __init__(
        self,
        *,
        config: LLMConfig | None = None,
        model: BaseChatModel | None = None,
    ) -> None:
        self._config = config or LLMConfig.from_env()
        self._model = model or self._build_model(self._config)

    @property
    def config(self) -> LLMConfig:
        return self._config

    @property
    def client(self) -> BaseChatModel:
        return self._model

    def _build_model(self, config: LLMConfig) -> BaseChatModel:
        """Create a LangChain chat model instance for the given config."""

        params: dict[str, Any] = {}
        if config.model is not None:
            params["model"] = config.model
        if config.max_tokens is not None:
            params["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            params["temperature"] = config.temperature

        if config.provider == LLMProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI")

            return ChatOpenAI(api_key=api_key, **params)

        if config.provider == LLMProvider.OLLAMA:
            # Use default Ollama model if not specified
            if "model" not in params:
                params["model"] = "qwen2.5:14b"
            
            if config.base_url:
                params["base_url"] = config.base_url
            return ChatOllama(**params)

        raise ValueError(f"Unsupported provider: {config.provider}")
    
    def invoke(
        self,
        messages: Iterable[BaseMessage] | Mapping[str, Any],
        config: RunnableConfig | None = None,
    ) -> Any:
        return self._model.invoke(messages, config)

    async def ainvoke(
        self,
        messages: Iterable[BaseMessage] | Mapping[str, Any],
        config: RunnableConfig | None = None,
    ) -> Any:
        return await self._model.ainvoke(messages, config)

    def stream(
        self,
        messages: Iterable[BaseMessage] | Mapping[str, Any],
        *,
        stream_mode: str | None = None,
        config: RunnableConfig | None = None,
    ) -> Iterable[Any]:
        return self._model.stream(messages, stream_mode=stream_mode, config=config)

