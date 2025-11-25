from src.graph import GraphManager
from src.tools.git_tools import GitToolbox
from src.tools.neo4j_tools import Neo4jGraphAdapter
from src.tools.unity_comms import UnityBridge


def test_neo4j_export_payload() -> None:
    graph = GraphManager()
    graph.add_node("a", label="Agent")
    graph.add_edge("a", "b")
    adapter = Neo4jGraphAdapter(graph)
    payload = adapter.export_payload()
    assert payload["nodes"][0]["id"] == "a"
    assert payload["edges"][0]["source"] == "a"
    assert payload["edges"][0]["target"] == "b"


def test_git_commit_message() -> None:
    git = GitToolbox()
    message = git.build_commit_message("feat", "Add planner", ["- add tests"])
    assert message.startswith("feat: Add planner")
    assert "- add tests" in message


def test_unity_bridge_queue() -> None:
    bridge = UnityBridge()
    bridge.queue_message("Update asset")
    assert bridge.pending() == 1
    assert bridge.dequeue_message() == "Update asset"
    assert bridge.dequeue_message() is None
