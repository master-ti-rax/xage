from src.graph import GraphManager


def test_add_node_and_edge() -> None:
    graph = GraphManager()
    graph.add_node("agent", role="planner")
    graph.add_node("task", role="job")
    graph.add_edge("agent", "task")

    assert graph.has_node("agent")
    assert graph.has_edge("agent", "task")

    snapshot = graph.snapshot()
    assert snapshot["nodes"]["agent"]["role"] == "planner"
    assert snapshot["edges"]["agent"] == ["task"]


def test_find_nodes_by() -> None:
    graph = GraphManager()
    graph.add_node("A", kind="agent")
    graph.add_node("B", kind="task")
    graph.add_node("C", kind="agent")

    agents = graph.find_nodes_by(kind="agent")
    assert sorted(agents) == ["A", "C"]
