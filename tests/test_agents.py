from src.agents.asset_manager import AssetManagerAgent
from src.agents.orchestrator import OrchestratorAgent
from src.main import bootstrap_default_context


def test_orchestrator_executes_plan() -> None:
    context = bootstrap_default_context()
    orchestrator = OrchestratorAgent(context)
    plan = orchestrator.run("Import assets; Validate data")

    assert len(plan) >= 1
    assert context.state.plan == plan
    assert context.state.assets
    assert not context.state.errors


def test_asset_manager_updates_assets() -> None:
    context = bootstrap_default_context()
    manager = AssetManagerAgent(context)
    record = manager.ensure_asset("hero", "mesh", quality="high")
    assert record.metadata["quality"] == "high"

    updated = manager.ensure_asset("hero", "mesh", lod="lod0")
    assert updated.metadata["lod"] == "lod0"
    assert updated.metadata["quality"] == "high"
