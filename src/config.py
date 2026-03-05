"""Application configuration."""

import logging
import os
import sys
from dataclasses import dataclass


def configure_logging(level: str | None = None) -> None:
    """Configure the root logger for the xage package.

    Call once at application startup (e.g. in main.py or test_workflow.py).

    The log level can be set via the ``LOG_LEVEL`` env-var (DEBUG, INFO,
    WARNING, ERROR) or passed explicitly.  Defaults to INFO.

    Format includes timestamp, logger name, level, and message so that
    tracebacks from ``logger.exception()`` are immediately useful.
    """
    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    logging.basicConfig(
        level=getattr(logging, resolved_level, logging.INFO),
        format="%(asctime)s | %(name)-36s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
        force=True,  # reconfigure if already set
    )

    # Silence noisy third-party loggers unless we're in DEBUG
    if resolved_level != "DEBUG":
        for noisy in (
            "httpx",
            "httpcore",
            "urllib3",
            "langchain",
            "langchain_core",
            "langchain_ollama",
            "langsmith",
            "openai",
        ):
            logging.getLogger(noisy).setLevel(logging.WARNING)


@dataclass(frozen=True)
class GraphConfig:
    """Configuration for the LangGraph workflow."""
    recursion_limit: int = 50

    @classmethod
    def from_env(cls) -> "GraphConfig":
        """Create configuration from environment variables."""
        try:
            limit = int(os.getenv("GRAPH_RECURSION_LIMIT", "50"))
        except ValueError:
            limit = 50
            
        return cls(recursion_limit=limit)
