from __future__ import annotations

from pathlib import Path

from src.graph import GraphManager
from src.tools.neo4j_tools import Neo4jGraphAdapter


def build_sample_graph() -> GraphManager:
    graph = GraphManager()
    graph.add_node("Agent:Planner", kind="agent", role="planner")
    graph.add_node("Task:CreatePlan", kind="task", status="pending")
    graph.add_node("Task:ValidatePlan", kind="task", status="pending")
    graph.add_edge("Agent:Planner", "Task:CreatePlan")
    graph.add_edge("Task:CreatePlan", "Task:ValidatePlan")
    return graph


def main() -> None:
    graph = build_sample_graph()
    adapter = Neo4jGraphAdapter(graph)
    payload = adapter.export_payload()
    output_path = Path("data/local_db/neo4j_seed.json")
    adapter.write_payload_to_file(payload, output_path)
    print(f"Seed graph exported to {output_path}")


if __name__ == "__main__":
    main()
