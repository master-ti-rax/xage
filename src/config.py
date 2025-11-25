"""Application configuration."""

import os
from dataclasses import dataclass

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
