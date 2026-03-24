"""LangChain-compatible tool definitions for agents."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from langchain.tools import tool

logger = logging.getLogger(__name__)

import requests

from src.tools.git_tools import GitToolbox
from src.tools.sketchfab_tools import SketchfabClient


# ============================================================================
# Tool instances (can be initialized with config as needed)
# ============================================================================

_git_tools = GitToolbox()


# ============================================================================
# C# Diagnostics Tools
# ============================================================================

@tool
def fetch_csharp_errors(code: str, file_path: str | None = None) -> dict[str, Any]:
    """Retrieve compiler diagnostics for generated C# code.

    Args:
        code: Complete C# source code to validate (used if file_path is None).
        file_path: Optional path to the C# file to validate. If provided, this file is checked instead of creating a temp file.

    Returns:
        Dict with compilation diagnostics.
    """
    if not file_path and not code.strip():
        return {
            "status": "error",
            "message": "No C# code or file path provided for validation.",
        }

    tmp_path = None
    target_path = ""

    if file_path:
        target_path = file_path
        if not os.path.exists(target_path):
            return {
                "status": "error",
                "message": f"Provided file path does not exist: {target_path}",
            }
    else:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        target_path = tmp_path

    try:
        # Path to the RoslynValidator project
        validator_dir = Path(__file__).parent / "RoslynValidator"
        project_path = validator_dir / "RoslynValidator.csproj"
        
        # Try to run with dotnet run
        # Note: This requires dotnet SDK to be installed in the environment
        cmd = ["dotnet", "run", "--project", str(project_path), "--", target_path]
        
        # Force English output for .NET CLI
        env = os.environ.copy()
        env["DOTNET_CLI_UI_LANGUAGE"] = "en-US"

        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False,
            env=env
        )
        
        if result.returncode != 0:
            # If dotnet is missing or fails to run
            return {
                "status": "error",
                "message": "Failed to run C# validator. Ensure dotnet SDK is installed.",
                "details": result.stderr or result.stdout or "Unknown error"
            }
            
        # Parse the JSON output from the validator
        try:
            # The output might contain build logs before the JSON. 
            # We should look for the last line or try to find the JSON object.
            # However, dotnet run -v q (quiet) might help, or we can just parse the output.
            # Let's try to find the JSON part.
            output = result.stdout.strip()
            # Find the start of the JSON object
            json_start = output.find('{')
            if json_start != -1:
                json_str = output[json_start:]
                validation_result = json.loads(json_str)
                return validation_result
            else:
                return {
                    "status": "error",
                    "message": "No JSON output found from validator",
                    "raw_output": output
                }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid output from C# validator",
                "raw_output": result.stdout
            }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "dotnet command not found. Please install .NET SDK."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error during validation: {str(e)}"
        }
    finally:
        # Clean up temp file if we created one
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================================
# Neo4j Knowledge Graph Tools
# ============================================================================

@tool
def query_knowledge_graph(query: str) -> dict[str, Any]:
    """Query the Neo4j knowledge graph for information about Unity components and patterns.

    Args:
        query: Natural language question about Unity components, methods, or patterns.
        Example: "How to implement a grab and place logic for a process step"

    Returns:
        Dict with query results including relevant components and instructions.
    """
    # TODO: Implement Neo4j query integration
    logger.warning("query_knowledge_graph is not yet implemented, returning empty results for: %s", query)
    return {
        "status": "not_implemented",
        "query": query,
        "results": [],
    }


# ============================================================================
# Sketchfab 3D Model Search Tools
# ============================================================================

@tool
def download_sketchfab_models(model_names: list[str], search_limit: int = None, download_limit: int = None) -> dict[str, Any]:
    """Download Sketchfab 3D models matching the given model names."""

    if not model_names:
        return {"status": "error", "message": "At least one model name is required"}

    token = os.getenv("SKETCHFAB_API_KEY", "")
    download_dir = Path(os.getenv("SKETCHFAB_DOWNLOAD_DIR", "artifacts/sketchfab"))

    client = SketchfabClient(token, requests.Session(), download_dir)
    downloaded_paths = client.download_models(model_names, search_limit, download_limit)

    return {
        "status": "ok",
        "model_names": model_names,
        "downloaded_files": [str(path) for path in downloaded_paths],
    }


# ============================================================================
# Unity Scene Query Tools
# ============================================================================

@tool
def query_unity_scene(query_command: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Query the live Unity scene to check object states and components.

    Args:
        query_command: Type of query to perform.
            Examples: "CheckObjectExists", "CheckComponentAttached", "CheckProcessStepConfigured"
        parameters: Query parameters.
            Examples: {"object_name": "SafetyGloves", "component_name": "VirooGrabbable"}

    Returns:
        Dict with query results from the Unity scene.
    """
    # TODO: Implement Unity scene query via bridge
    logger.warning("query_unity_scene is not yet implemented, returning empty results for: %s", query_command)
    return {
        "status": "not_implemented",
        "command": query_command,
        "parameters": parameters,
    }


# ============================================================================
# Git Commit Tools
# ============================================================================

@tool
def build_git_commit_message(
    commit_type: str,
    summary: str,
    bullet_points: list[str] | None = None,
) -> str:
    """Build a structured git commit message.
    
    Args:
        commit_type: Type of commit (e.g., "feat", "fix", "docs")
        summary: Brief summary of the change
        bullet_points: Optional list of detailed change points
    
    Returns:
        Formatted git commit message.
    """
    return _git_tools.build_commit_message(commit_type, summary, bullet_points)


@tool
def summarize_git_changes(changes: list[dict[str, Any]]) -> str:
    """Summarize git changes with timestamps and line counts.
    
    Args:
        changes: List of dicts with 'path', 'added', and 'removed' keys
    
    Returns:
        Formatted summary of changes.
    """
    return _git_tools.summarize_changes(changes)


# ============================================================================
# Orchestrator Tools
# ============================================================================

@tool
def get_next_uncompleted_activity(
    educational_plan: dict[str, Any],
    completed_activity_ids: list[str],
) -> dict[str, Any]:
    """Get the first activity in the educational plan that has not been completed yet.
    
    Args:
        educational_plan: The educational plan containing modules with steps.
        completed_activity_ids: List of activity IDs that have been completed.
    
    Returns:
        Dict with 'task_id' and 'description' keys for the next activity,
        or 'ALL_TASKS_COMPLETE' if all activities are done.
    """
    # Extract all steps from all modules in the educational plan
    all_steps = []
    
    # Check if steps are at top level (flat structure)
    if "steps" in educational_plan:
        all_steps = educational_plan["steps"]
    # Check if steps are nested in modules (nested structure)
    elif "modules" in educational_plan:
        for module in educational_plan["modules"]:
            module_steps = module.get("steps", [])
            all_steps.extend(module_steps)
    
    if not all_steps:
        return {
            "task_id": "NO_STEPS_FOUND",
            "description": "No steps found in the educational plan."
        }
    
    # Find the first step that hasn't been completed
    for step in all_steps:
        step_id = step.get("id", "")
        if step_id not in completed_activity_ids:
            return {
                "task_id": step_id,
                "description": step.get("description", "")
            }
    
    # All tasks are complete
    return {
        "task_id": "ALL_TASKS_COMPLETE",
        "description": "All tasks in the Educational Plan are finished."
    }


# ============================================================================
# Tool Collections for Different Agents
# ============================================================================

def get_planner_tools() -> list:
    """Tools available to the Planner Agent."""
    return []


def get_executor_tools() -> list:
    """Tools available to the Executor Agent."""
    return []  # Executor generates code, doesn't use tools


def get_validator_tools() -> list:
    """Tools available to the Validator Agent."""
    return [
        fetch_csharp_errors,
    ]


def get_asset_manager_tools() -> list:
    """Tools available to the Asset Manager Agent."""
    return [
        query_knowledge_graph,
        download_sketchfab_models,
    ]


def get_orchestrator_tools() -> list:
    """Tools available to the Orchestrator Agent."""
    return [
        get_next_uncompleted_activity,
    ]


__all__ = [
    "query_knowledge_graph",
    "download_sketchfab_models",
    "query_unity_scene",
    "build_git_commit_message",
    "summarize_git_changes",
    "fetch_csharp_errors",
    "get_next_uncompleted_activity",
    "get_planner_tools",
    "get_executor_tools",
    "get_validator_tools",
    "get_asset_manager_tools",
    "get_orchestrator_tools",
]
