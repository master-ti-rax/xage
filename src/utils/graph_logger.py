import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

GRAPH_LOG_FILE = Path("artifacts/graph_execution_log.json")


class GraphExecutionLogger:
    """
    Records the execution of the workflow as a graph (nodes and edges).
    This output can be directly ingested into graph databases (e.g., Neo4j).
    """

    def __init__(self, run_id: str = None):
        self.run_id = run_id or datetime.now().isoformat()
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        # Ensure directory exists
        GRAPH_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_existing()

    def _load_existing(self):
        """Loads existing graph log if we are appending to it, mostly for multiple runs."""
        pass  # We will just overwrite or append at the top level for now.

    def log_node(self, node_id: str, agent_name: str, status: str, inputs: Any, outputs: Any, metadata: Dict[str, Any] = None):
        """
        Logs a node execution (an agent running).
        """
        node_record = {
            "id": node_id,
            "type": "AgentExecution",
            "run_id": self.run_id,
            "agent_name": agent_name,
            "status": status,
            "inputs": self._sanitize(inputs),
            "outputs": self._sanitize(outputs),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.nodes.append(node_record)
        self.save()

    def log_edge(self, source_id: str, target_id: str, edge_type: str = "NEXT", properties: Dict[str, Any] = None):
        """
        Logs a directed edge indicating workflow transition.
        """
        edge_record = {
            "source": source_id,
            "target": target_id,
            "type": edge_type,
            "run_id": self.run_id,
            "properties": properties or {},
            "timestamp": datetime.now().isoformat()
        }
        self.edges.append(edge_record)
        self.save()

    def _sanitize(self, data: Any) -> Any:
        try:
            # Simple check if serializable
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            if hasattr(data, "model_dump"):
                try:
                    return data.model_dump()
                except Exception:
                    pass
            elif isinstance(data, dict):
                return {k: self._sanitize(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self._sanitize(v) for v in data]
            return str(data)

    def save(self):
        """Saves the current state of the execution graph to a JSON file."""
        data = {
            "run_id": self.run_id,
            "nodes": self.nodes,
            "edges": self.edges,
            "duration_seconds": time.time() - self.start_time
        }
        try:
            with open(GRAPH_LOG_FILE, "w", encoding="utf-8") as f:
                json.dumps(data) # Check if fail
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save graph execution log: {e}")

# Global instance for easy import if needed
graph_execution_logger = GraphExecutionLogger()
