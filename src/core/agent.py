"""LangChain v1.0 compatible agent base classes."""

from __future__ import annotations

from typing import Any, Iterable, MutableSequence, Sequence

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableConfig


class BaseAgent:
    """Common foundation for orchestrator, planner, validator, etc.

    This class wraps ``langchain.agents.create_agent`` (introduced in LangChain
    1.0) so that agents built for this project inherit the same capabilities as
    the upstream runtime. It keeps provider selection outside of agent logic and
    exposes a simple API for invoking, streaming, and reconfiguring the agent.
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        model: str | BaseChatModel | None = None,
        tools: Sequence[Any] | None = None,
        system_prompt: str | None = None,
        middleware: Sequence[Any] | None = None,
        state_schema: type | None = None,
    ) -> None:
        self.name = name or self.__class__.__name__
        self._model = model
        self._tools: MutableSequence[Any] = list(tools or [])
        self._system_prompt = system_prompt
        self._middleware: MutableSequence[Any] = list(middleware or [])
        self._state_schema = state_schema
        self._agent = self._build_agent()

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------

    def _build_agent(self) -> Runnable:
    
        return create_agent(
            model=self._model,
            tools=self._tools,
            system_prompt=self._system_prompt,
            middleware=self._middleware,
            state_schema=self._state_schema,
        )

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    @property
    def runnable(self) -> Runnable:
        return self._agent

    @property
    def model(self) -> str | BaseChatModel:
        return self._model

    def invoke(
        self,
        state: dict[str, Any],
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        return self._agent.invoke(state, config)

    async def ainvoke(
        self,
        state: dict[str, Any],
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        return await self._agent.ainvoke(state, config)

    def stream(
        self,
        state: dict[str, Any],
        *,
        stream_mode: str | None = None,
        config: RunnableConfig | None = None,
    ) -> Iterable[dict[str, Any]]:
        return self._agent.stream(state, stream_mode=stream_mode, config=config)

    def messages(self, state: dict[str, Any]) -> Sequence[BaseMessage]:
        return state.get("messages", [])

