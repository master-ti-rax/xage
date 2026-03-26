"""LangGraph workflow orchestration for the multi-agent system.

This module implements the core workflow using LangGraph's StateGraph API.
It defines the execution flow: Orchestrator -> Planner -> Asset Manager -> 
Planner -> Executor -> Validator, with feedback loops for refinement.
"""

from __future__ import annotations

import sys
import json
import re
import os
import csv
import uuid
from typing import Any, TypedDict
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from src.agents.asset_manager import AssetManager
from src.agents.executor import ExecutorAgent
from src.agents.orchestrator import OrchestratorAgent
from src.agents.planner import PlannerAgent
from src.agents.validator import ValidatorAgent
from src.core.llm import LLMConfig
from src.config import GraphConfig
from src.state import ExecutionState
from src.utils.cleaning import clean_agent_output
from src.utils.code_assembler import insert_step_code, replace_step_code, extract_step_code, clean_step_output
from src.utils.graph_logger import graph_execution_logger


# ============================================================================
# Logging Utilities
# ============================================================================

def log_node_start(node_name: str, state: dict[str, Any]) -> None:
    """Log when a node starts executing."""
    current_module = state.get("current_module")
    module_id = current_module.get("module_id") if current_module else "None"
    print(f"\n{'─'*70}")
    print(f"→ NODE: {node_name:20} [Module: {module_id}]")
    print(f"{'─'*70}")


def log_node_end(node_name: str, result: dict[str, Any]) -> None:
    """Log when a node completes."""
    updates = list(result.keys())
    print(f"✓ {node_name:20} Updated: {updates}")


def log_agent_output(agent_name: str, output: Any) -> None:
    """Log agent output in a clean format."""
    print(f"\n📊 {agent_name} Output:")
    
    if isinstance(output, dict):
        for key, value in output.items():
            if isinstance(value, str):
                # Truncate long strings
                if len(value) > 120:
                    print(f"   • {key}: {value[:120]}...")
                else:
                    print(f"   • {key}: {value}")
            elif isinstance(value, list):
                if value:
                    print(f"   • {key}: {len(value)} items")
                    for item in value[:3]:  # Show first 3 items
                        item_str = str(item)
                        if len(item_str) > 100:
                            print(f"       - {item_str[:100]}...")
                        else:
                            print(f"       - {item_str}")
                    if len(value) > 3:
                        print(f"       ... and {len(value) - 3} more")
                else:
                    print(f"   • {key}: []")
            else:
                print(f"   • {key}: {value}")
    elif isinstance(output, str):
        # For string outputs like from Planner/Executor
        if len(output) > 200:
            print(f"   Content (first 200 chars):")
            print(f"   {output[:200]}...")
        else:
            print(f"   Content:")
            print(f"   {output}")
    else:
        print(f"   {str(output)[:200]}")


def log_raw_agent_response(agent_name: str, output: Any) -> None:
    """Log the raw agent response and wait for user input to continue."""
    print(f"\n{'='*70}")
    print(f"🔍 RAW OUTPUT FROM: {agent_name}")
    print(f"{'='*70}")
    print(f"Type: {type(output).__name__}")
    print(f"{'─'*70}")

    print(output)
    
    print(f"{'─'*70}")
    print(f"📏 Length: {len(str(output))} characters")
    print(f"{'='*70}")
    
    try:
        #input("\n⏸️  Press ENTER to continue...")
        pass
    except EOFError:
        pass
    print()


# ============================================================================
# Dataset Utilities
# ============================================================================

def append_row_to_csv(row: dict, filepath: str = "dataset.csv") -> None:
    """Append a single row to the CSV dataset file."""
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ============================================================================
# State Schema
# ============================================================================

class WorkflowState(TypedDict, total=False):
    """State schema for the multi-agent workflow."""

    # Educational plan input
    educational_plan: dict[str, Any]
    segmented_modules: list[dict[str, Any]]
    plan_summary: dict[str, Any] | None

    # Module-level tracking (owned by Orchestrator)
    completed_modules: list[str]
    current_module: dict[str, Any] | None

    # Task-level tracking within a module (owned by Planner)
    execution_plan: str | None
    execution_plan_dict: dict[str, Any] | None
    current_task_index: int | None
    current_task: dict[str, Any] | None
    completed_tasks: list[str]

    # Asset retrieval
    asset_request: dict[str, Any] | None
    retrieved_assets: dict[str, Any] | None

    # Executor / Validator
    executor_payload: dict[str, Any] | None
    generated_code: str | None
    generated_file_path: str | None
    validation_result: dict[str, Any] | None

    # Dataset
    current_step_data: dict[str, Any]
    dataset: list[dict[str, Any]]

    # Bookkeeping
    history: list[str]
    errors: list[str]
    last_node_id: str | None


# ============================================================================
# Agent Instances
# ============================================================================

def _init_agents(llm_config: LLMConfig | None = None) -> dict[str, Any]:
    """Initialize all agents with optional LLM config."""
    base_config = llm_config or LLMConfig.from_env()
    return {
        "orchestrator": OrchestratorAgent(llm_config=base_config.with_updates(model=os.getenv("ORCHESTRATOR_MODEL"))),
        "asset_manager": AssetManager(),
        "planner": PlannerAgent(llm_config=base_config.with_updates(model=os.getenv("PLANNER_MODEL"))),
        "executor": ExecutorAgent(llm_config=base_config.with_updates(model=os.getenv("EXECUTOR_MODEL"))),
        "validator": ValidatorAgent(llm_config=base_config.with_updates(model=os.getenv("VALIDATOR_MODEL"))),
    }


# ============================================================================
# Node Functions
# ============================================================================

def orchestrator_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Orchestrator Node: Determine the next module from the Educational Plan."""
    node_id = str(uuid.uuid4())
    last_node_id = state.get("last_node_id")
    if last_node_id:
        graph_execution_logger.log_edge(last_node_id, node_id, edge_type="NEXT")
        
    log_node_start("Orchestrator", state)
    
    orchestrator = agents["orchestrator"]
    completed_modules = state.get("completed_modules", [])
    segmented_modules = state.get("segmented_modules")
    plan_summary = state.get("plan_summary")

    if not segmented_modules:
        segmented_modules = orchestrator.segment_plan(state["educational_plan"])

    if not plan_summary:
        plan_summary = orchestrator.summarize_plan(state["educational_plan"])
    
    inputs_for_log = {
        "segmented_modules": segmented_modules,
        "completed_modules": completed_modules
    }
    
    orchestrator._call_log.clear()
    result = orchestrator.get_next_module(
        segmented_modules=segmented_modules,
        completed_modules=completed_modules,
    )
    log_agent_output("Orchestrator", result)

    graph_execution_logger.log_node(node_id, "Orchestrator", "COMPLETED", inputs_for_log, result, prompts=list(orchestrator._call_log))
    orchestrator._call_log.clear()
    
    module_info = {
        "module_id": result.get("module_id"),
        "description": result.get("description"),
    }
    history = state.get("history", [])
    module_id = module_info.get('module_id', 'UNKNOWN')
    
    # Check if all modules are complete
    if module_id == "ALL_MODULES_COMPLETE":
        history.append("Orchestrator found all modules complete")
        return {
            "segmented_modules": segmented_modules,
            "plan_summary": plan_summary,
            "current_module": None,
            "history": history,
            "last_node_id": node_id,
        }
    
    # Safeguard: if module is already in completed list, something is wrong - mark as complete
    if module_id in completed_modules:
        history.append("Orchestrator found module already completed")
        return {
            "segmented_modules": segmented_modules,
            "plan_summary": plan_summary,
            "current_module": None,
            "history": history,
            "last_node_id": node_id,
        }

    module_payload = result.get("description")
    if isinstance(module_payload, dict):
        handoff = orchestrator.build_module_handoff(
            module=module_payload,
            plan_summary=plan_summary,
        )
        module_info["description"] = handoff.get("planner_brief", handoff)
    
    # Dataset: update current_step_data with module info
    current_step_data = state.get("current_step_data", {})
    description = module_info.get("description")
    current_step_data.update({
        "module_id": module_id,
        "module_title": description.get("module_title") if isinstance(description, dict) else None,
    })
    
    history.append("Orchestrator returned the educational module")
    
    return {
        "segmented_modules": segmented_modules,
        "plan_summary": plan_summary,
        "current_module": module_info,
        "current_step_data": current_step_data,
        "history": history,
        "last_node_id": node_id,
    }


def planner_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Planner Node: Coordinate execution steps and required assets."""
    node_id = str(uuid.uuid4())
    last_node_id = state.get("last_node_id")
    if last_node_id:
        graph_execution_logger.log_edge(last_node_id, node_id, edge_type="NEXT")
        
    log_node_start("Planner", state)

    if not state.get("current_module"):
        return {"last_node_id": node_id}

    planner = agents["planner"]
    history = state.get("history", [])
    last_event = history[-1] if history else ""

    # Case 1: New Module from Orchestrator -> Create Plan
    if last_event == "Orchestrator returned the educational module":
        module_description = state["current_module"].get("description", "")
        if isinstance(module_description, dict):
            module_description = json.dumps(module_description, indent=2)
        
        inputs_for_log = {"module_description": module_description}
        planner._call_log.clear()
        execution_plan_dict = planner.create_execution_plan(
            module_description=module_description
        )

        execution_plan_json = json.dumps(execution_plan_dict, indent=2)

        num_tasks = len(execution_plan_dict.get("implementation_tasks", []))
        overview = execution_plan_dict.get("overview", "No overview")
        log_agent_output("Planner", f"Plan Overview: {overview}\nTasks: {num_tasks}")

        graph_execution_logger.log_node(node_id, "Planner - Create Plan", "COMPLETED", inputs_for_log, execution_plan_dict, prompts=list(planner._call_log))
        planner._call_log.clear()

        implementation_steps = execution_plan_dict.get("implementation_steps", [])
        if not implementation_steps:
            history.append("Planner generated an empty execution plan")
            return {
                "execution_plan": execution_plan_json,
                "execution_plan_dict": execution_plan_dict,
                "history": history,
                "last_node_id": node_id,
            }

        current_task_index = 0
        current_task = implementation_steps[current_task_index]
        asset_request = {
            "required_assets": current_task.get("required_assets"),
            "required_knowledge": current_task.get("required_knowledge"),
        }

        # Dataset: update current_step_data with first implementation step
        current_step_data = state.get("current_step_data", {})
        current_step_data.update({
        "step_id": current_task.get("parent_step"),
        "step_title": current_task.get("parent_step_title"),
        "step_description": current_task.get("parent_step_description"),
        "implementation_sub_step_id": current_task.get("step_id"),
        "implementation_sub_step_title": current_task.get("title"),
        "implementation_sub_step_description": current_task.get("description"),
        "implementation_sub_step_required_assets": current_task.get("required_assets"),
        "implementation_sub_step_required_template": current_task.get("required_templates"),
        })

        history.append("Planner requested assets from Asset Manager")

        return {
            "execution_plan": execution_plan_json,
            "execution_plan_dict": execution_plan_dict,
            "current_task_index": current_task_index,
            "current_task": current_task,
            "completed_tasks": [],
            "asset_request": asset_request,
            "current_step_data": current_step_data,
            "history": history,
            "last_node_id": node_id,
        }

    # Case 2: Assets Returned -> Send to Executor
    elif last_event == "Asset Manager returned resources to Planner":
        retrieved_assets = state.get("retrieved_assets")
        current_task = state.get("current_task")
        current_task_index = state.get("current_task_index")
        execution_plan_dict = state.get("execution_plan_dict", {})
        scene_hierarchy = execution_plan_dict.get("scene_hierarchy", {})

        inputs_for_log = {
            "current_task": current_task,
            "retrieved_assets": retrieved_assets
        }

        if current_task is not None:
            executor_payload = {
                "implementation_step": current_task,
                "retrieved_assets": retrieved_assets,
                "task_index": current_task_index,
                "scene_hierarchy": scene_hierarchy,
            }

            log_agent_output(
                "Planner",
                "Prepared implementation step with retrieved assets for Executor",
            )

            graph_execution_logger.log_node(node_id, "Planner - Prepare Executor Payload", "COMPLETED", inputs_for_log, executor_payload)

            history.append("Planner sent implementation step to Executor")

            return {
                "executor_payload": executor_payload,
                "retrieved_assets": None,
                "asset_request": None,
                "history": history,
                "last_node_id": node_id,
            }

    # Case 3: Task validated -> advance to next task or complete module
    elif last_event == "Executor confirmed implementation completion":
        current_task_index = state.get("current_task_index", 0)
        execution_plan_dict = state.get("execution_plan_dict")
        implementation_steps = execution_plan_dict.get("implementation_steps", [])

        inputs_for_log = {
            "current_task_index": current_task_index,
            "completed_tasks": state.get("completed_tasks")
        }

        # Mark current task as completed
        completed_tasks = list(state.get("completed_tasks") or [])
        current_task = state.get("current_task") or {}
        task_id = str(current_task.get("step_id") or current_task_index)
        if task_id and task_id not in completed_tasks:
            completed_tasks.append(task_id)

        next_index = current_task_index + 1

        if next_index >= len(implementation_steps):
            # All tasks for this module are done -> mark module complete
            completed_modules = list(state.get("completed_modules") or [])
            module_id = (state.get("current_module") or {}).get("module_id")
            module_id_str = str(module_id) if module_id is not None else ""
            if module_id_str and module_id_str not in completed_modules:
                completed_modules.append(module_id_str)

            history.append("Planner determined all tasks for module are complete")
            outputs_for_log = {"status": "module_complete", "completed_modules": completed_modules}
            graph_execution_logger.log_node(node_id, "Planner - Advance Task", "COMPLETED", inputs_for_log, outputs_for_log)

            return {
                "completed_modules": completed_modules,
                "completed_tasks": completed_tasks,
                "current_module": None,
                "current_task": None,
                "validation_result": None,
                "executor_payload": None,
                "history": history,
                "last_node_id": node_id,
            }

        # Advance to next task
        next_task = implementation_steps[next_index]
        asset_request = {
            "required_assets": next_task.get("required_assets"),
            "required_knowledge": next_task.get("required_knowledge"),
        }

        # Dataset: update current_step_data with next implementation step
        current_step_data = state.get("current_step_data", {})
        current_step_data.update({
        "step_id": next_task.get("parent_step"),
        "step_title": next_task.get("parent_step_title"),
        "step_description": next_task.get("parent_step_description"),
        "implementation_sub_step_id": next_task.get("step_id"),
        "implementation_sub_step_title": next_task.get("title"),
        "implementation_sub_step_description": next_task.get("description"),
        "implementation_sub_step_required_assets": next_task.get("required_assets"),
        "implementation_sub_step_required_template": next_task.get("required_templates"),
        })

        history.append(f"Planner advancing to task {next_index + 1}")
        history.append("Planner requested assets from Asset Manager")

        outputs_for_log = {"status": "next_task", "next_task_index": next_index, "asset_request": asset_request}
        graph_execution_logger.log_node(node_id, "Planner - Advance Task", "COMPLETED", inputs_for_log, outputs_for_log)

        return {
            "current_task_index": next_index,
            "current_task": next_task,
            "completed_tasks": completed_tasks,
            "asset_request": asset_request,
            "validation_result": None,
            "executor_payload": None,
            "current_step_data": current_step_data,
            "history": history,
            "last_node_id": node_id,
        }

    return {"last_node_id": node_id}


def asset_manager_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Asset Manager Node: Retrieve required knowledge and 3D models."""
    node_id = str(uuid.uuid4())
    last_node_id = state.get("last_node_id")
    if last_node_id:
        graph_execution_logger.log_edge(last_node_id, node_id, edge_type="NEXT")
        
    log_node_start("Asset Manager", state)

    asset_request = state.get("asset_request")
    if not asset_request:
        return {"last_node_id": node_id}

    asset_manager = agents["asset_manager"]
    required_assets = asset_request.get("required_assets") or []
    required_knowledge = asset_request.get("required_knowledge") or []
    
    inputs_for_log = {
        "required_assets": required_assets,
        "required_knowledge": required_knowledge
    }
    
    if not isinstance(required_assets, list):
        print("Error: required_assets is not a list:")
        print(required_assets)
        required_assets = []
    if not isinstance(required_knowledge, list):
        print("Error: required_knowledge is not a list:")
        print(required_knowledge)
        required_knowledge = []

    retrieved_assets = asset_manager.retrieve(
        assets=required_assets,
        knowledge=required_knowledge
    )

    log_raw_agent_response("Asset Manager", retrieved_assets)

    graph_execution_logger.log_node(node_id, "Asset Manager", "COMPLETED", inputs_for_log, retrieved_assets)
    
    num_knowledge = len(retrieved_assets.get("retrieved_knowledge", []))
    num_models = len(retrieved_assets.get("retrieved_models", []))
    summary = retrieved_assets.get("summary", "Resources retrieved")
    log_agent_output("Asset Manager", f"{summary}\nKnowledge items: {num_knowledge}, Model searches: {num_models}")
    
    history = state.get("history", [])
    history.append("Asset Manager returned resources to Planner")

    return {
        "retrieved_assets": retrieved_assets,
        "history": history,
        "last_node_id": node_id,
    }


_INITIAL_TEMPLATE = """\
using UnityEngine;
using System.Collections.Generic;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;
using Viroo.Interactions.Grab;
using Viroo.Interactions.XRInteractionToolkit;

public class SceneLogicDavide
{
    static void CreateScene()
    {
        // Initialize environment
        EnvironmentHelper.SetupStandardScenary();

        // STEP_INSERTION_POINT
    }
}
"""


def _resolve_scripts_dir() -> Path | None:
    """Return the resolved Unity scripts directory, or None if not configured."""
    unity_scripts_path = os.getenv("UNITY_SCRIPTS_PATH")
    if unity_scripts_path:
        p = Path(unity_scripts_path) if os.path.isabs(unity_scripts_path) else Path(os.path.abspath(unity_scripts_path))
        p.mkdir(parents=True, exist_ok=True)
        return p

    unity_project_path = os.getenv("UNITY_PROJECT_PATH")
    if unity_project_path:
        p = Path(unity_project_path) if os.path.isabs(unity_project_path) else Path(os.path.abspath(unity_project_path))
        scripts_dir = p / "Assets" / "Scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        return scripts_dir

    return None


def executor_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Executor Node: Generate incremental C# code for an implementation step."""
    node_id = str(uuid.uuid4())
    last_node_id = state.get("last_node_id")
    if last_node_id:
        graph_execution_logger.log_edge(last_node_id, node_id, edge_type="NEXT")

    log_node_start("Executor", state)

    history = state.get("history", [])
    last_event = history[-1] if history else ""
    executor = agents["executor"]

    validation_feedback = None

    # Case 1: Validation Feedback (from Validator)
    if last_event == "Validator reported validation result to Executor":
        validation_result = state.get("validation_result")
        if validation_result and validation_result.get("validation_status") == "Success":
            history.append("Executor confirmed implementation completion")
            print("  ✓ Executor confirmed task completion")
            graph_execution_logger.log_node(node_id, "Executor - Confirmation", "COMPLETED", {"validation_result": validation_result}, {"status": "confirmed_completion"})
            return {"history": history, "last_node_id": node_id}

        # Failure case — Refinement
        if validation_result:
            validation_feedback = (
                f"Validation Status: {validation_result.get('validation_status')}\n"
                f"Reasoning: {validation_result.get('reasoning')}\n"
                f"Checks: {validation_result.get('checks_performed')}"
            )

    # Case 2: Initial Implementation (from Planner)
    elif last_event == "Planner sent implementation step to Executor":
        validation_feedback = None

    else:
        return {"last_node_id": node_id}

    executor_payload = state.get("executor_payload")
    if not executor_payload:
        return {"last_node_id": node_id}

    implementation_step = executor_payload.get("implementation_step", {})
    retrieved_assets = executor_payload.get("retrieved_assets")
    scene_hierarchy = executor_payload.get("scene_hierarchy")

    task_index = executor_payload.get("task_index", 0)
    step_number = task_index + 1
    step_title = implementation_step.get("title", f"Step {step_number}") if isinstance(implementation_step, dict) else f"Step {step_number}"

    existing_code = state.get("generated_code") or _INITIAL_TEMPLATE

    step_code = None
    if validation_feedback:
        step_code = extract_step_code(existing_code, step_number)

    inputs_for_log = {
        "implementation_step": implementation_step,
        "existing_code_length": len(existing_code),
        "validation_feedback": validation_feedback,
        "step_number": step_number,
    }

    executor._call_log.clear()
    raw_output = executor.implement_step(
        implementation_step=implementation_step,
        existing_code=existing_code,
        retrieved_assets=retrieved_assets,
        validation_feedback=validation_feedback,
        scene_hierarchy=scene_hierarchy,
        step_code=step_code,
    )

    cleaned_step_code = clean_agent_output(str(raw_output), output_type="csharp")
    cleaned_step_code = clean_step_output(cleaned_step_code)

    log_raw_agent_response("Executor", cleaned_step_code)
    log_agent_output("Executor", cleaned_step_code)

    graph_execution_logger.log_node(node_id, "Executor - Implement Step", "COMPLETED", inputs_for_log, {"step_code_length": len(cleaned_step_code)}, prompts=list(executor._call_log))
    executor._call_log.clear()

    history = state.get("history", [])

    if not cleaned_step_code or len(cleaned_step_code.strip()) < 5:
        history.append("Executor failed to generate valid code")
        print("  ⚠️ Executor failed to generate valid code.")
        return {
            "generated_code": existing_code,
            "generated_file_path": None,
            "history": history,
            "last_node_id": node_id,
        }

    if validation_feedback and step_code is not None:
        try:
            assembled_code = replace_step_code(existing_code, step_number, cleaned_step_code)
        except ValueError:
            assembled_code = insert_step_code(existing_code, step_number, step_title, cleaned_step_code)
    else:
        assembled_code = insert_step_code(existing_code, step_number, step_title, cleaned_step_code)

    generated_file_path = None
    scripts_dir = _resolve_scripts_dir()
    if scripts_dir:
        try:
            target_file = scripts_dir / "SceneLogicDavide.cs"
            target_file.write_text(assembled_code, encoding="utf-8")
            generated_file_path = str(target_file)
            print(f"  ✓ Code written to: {generated_file_path}")
        except Exception as e:
            print(f"  ⚠️ Failed to write code to Unity project: {e}")
    else:
        print("  ⚠️ UNITY_PROJECT_PATH or UNITY_SCRIPTS_PATH not set, skipping file write.")

    # Dataset: update current_step_data with generated code
    current_step_data = state.get("current_step_data", {})
    generated_code_id = current_step_data.get("generated_code_id", 0) + 1
    current_step_data.update({
        "generated_code_id": generated_code_id,
        "generated_code": assembled_code,
    })

    history.append("Executor generated code for the implementation step")

    return {
        "generated_code": assembled_code,
        "generated_file_path": generated_file_path,
        "current_step_data": current_step_data,
        "history": history,
        "last_node_id": node_id,
    }


def validator_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Validator Node: QA test the completed task in the Unity scene."""
    node_id = str(uuid.uuid4())
    last_node_id = state.get("last_node_id")
    if last_node_id:
        graph_execution_logger.log_edge(last_node_id, node_id, edge_type="NEXT")
        
    log_node_start("Validator", state)

    if not state.get("current_task"):
        return {"last_node_id": node_id}
    
    validator = agents["validator"]
    generated_code = state.get("generated_code", "")
    generated_file_path = state.get("generated_file_path")
    
    executor_payload = state.get("executor_payload", {})
    retrieved_assets = executor_payload.get("retrieved_assets")
    implementation_step = executor_payload.get("implementation_step")
    
    inputs_for_log = {
        "generated_code_length": len(generated_code) if generated_code else 0,
        "implementation_step": implementation_step
    }
    
    validator._call_log.clear()
    validation_result = validator.validate_implementation_step(
        generated_code=generated_code,
        retrieved_assets=retrieved_assets,
        file_path=generated_file_path,
        implementation_step=implementation_step,
    )
    log_raw_agent_response("Validator", validation_result)
    log_agent_output("Validator", validation_result)

    graph_execution_logger.log_node(node_id, "Validator", "COMPLETED", inputs_for_log, validation_result, prompts=list(validator._call_log))
    validator._call_log.clear()

    # Dataset: update current_step_data with validation result and append to dataset
    current_step_data = state.get("current_step_data", {})
    validation_id = current_step_data.get("validation_id", 0) + 1
    current_step_data.update({
        "validation_id": validation_id,
        "validation_status": validation_result.get("validation_status"),
        "validation_checks": json.dumps(validation_result.get("checks_performed", [])),
        "validation_vector": validation_result.get("validation_vector"),
        "validation_reasoning": validation_result.get("reasoning"),
    })

    dataset = list(state.get("dataset", []))
    row = current_step_data.copy()
    dataset.append(row)

    dataset_path = os.getenv("DATASET_PATH", "dataset.csv")
    append_row_to_csv(row, filepath=dataset_path)

    history = state.get("history", [])
    history.append(
        f"Validator completed validation: "
        f"{validation_result.get('validation_status', 'Unknown')}"
    )
    history.append("Validator reported validation result to Executor")
    
    return {
        "validation_result": validation_result,
        "current_step_data": current_step_data,
        "dataset": dataset,
        "history": history,
        "last_node_id": node_id,
    }


# ============================================================================
# Conditional Routing Functions
# ============================================================================

def route(state: dict[str, Any]) -> str:
    """Determine the next node using the latest entry recorded in history."""
    history = state.get("history") or []
    last_event = history[-1] if history else ""

    routing_rules = [
        ("Orchestrator returned the educational module", "planner"),
        ("Orchestrator found all modules complete", "end"),
        ("Orchestrator found module already completed", "end"),
        ("Planner determined all tasks for module are complete", "orchestrator"),
        ("Planner requested assets from Asset Manager", "asset_manager"),
        ("Asset Manager returned resources to Planner", "planner"),
        ("Planner sent implementation step to Executor", "executor"),
        ("Executor generated code for the implementation step", "validator"),
        ("Validator reported validation result to Executor", "executor"),
        ("Executor confirmed implementation completion", "planner"),
    ]

    for marker, destination in routing_rules:
        if marker in last_event:
            return destination

    return "end"


def finalize_task_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Finalize a successfully completed task."""
    log_node_start("Finalize Task", state)
    
    task_id = state.get("current_module", {}).get("module_id", "")
    completed_modules = state.get("completed_modules", [])
    if task_id and task_id not in completed_modules:
        completed_modules.append(task_id)
    
    print(f"  ✓ Task {task_id} marked as complete")
    
    history = state.get("history", [])
    
    return {
        "completed_modules": completed_modules,
        "history": history,
    }


def record_failure_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Record a task validation failure."""
    log_node_start("Record Failure", state)
    
    validation_result = state.get("validation_result", {})
    errors = state.get("errors", [])
    errors.append(f"Task validation failed: {validation_result.get('reasoning')}")
    
    print(f"  ✗ Task validation failed")
    
    history = state.get("history", [])
    history.append("Validator reported validation failure to Executor")
    
    return {
        "errors": errors,
        "history": history,
    }


# ============================================================================
# Graph Construction
# ============================================================================

def build_workflow_graph(
    llm_config: LLMConfig | None = None,
) -> Any:
    """Build and compile the LangGraph workflow."""
    agents = _init_agents(llm_config)
    
    graph = StateGraph(WorkflowState)
    
    graph.add_node("orchestrator", lambda state: orchestrator_node(state, agents))
    graph.add_node("asset_manager", lambda state: asset_manager_node(state, agents))
    graph.add_node("planner", lambda state: planner_node(state, agents))
    graph.add_node("executor", lambda state: executor_node(state, agents))
    graph.add_node("validator", lambda state: validator_node(state, agents))
    
    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges("orchestrator", route, {"planner": "planner", "end": END})
    graph.add_conditional_edges("planner", route, {"orchestrator": "orchestrator", "asset_manager": "asset_manager", "executor": "executor", "end": END})
    graph.add_conditional_edges("asset_manager", route, {"planner": "planner", "end": END})
    graph.add_conditional_edges("executor", route, {"validator": "validator", "planner": "planner", "end": END})
    graph.add_conditional_edges("validator", route, {"executor": "executor", "end": END})
    
    return graph.compile()


# ============================================================================
# Execution Interface
# ============================================================================

def run_workflow(
    educational_plan: dict[str, Any],
    llm_config: LLMConfig | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """Run the complete workflow."""
    workflow = build_workflow_graph(llm_config)
    
    initial_state = {
        "educational_plan": educational_plan,
        "segmented_modules": [],
        "plan_summary": None,
        "completed_modules": [],
        "current_module": None,
        "execution_plan": None,
        "execution_plan_dict": None,
        "current_task_index": None,
        "current_task": None,
        "completed_tasks": [],
        "asset_request": None,
        "retrieved_assets": None,
        "executor_payload": None,
        "generated_code": None,
        "validation_result": None,
        "current_step_data": {
                # Orchestrator
                "educational_plan_id": None,
                "module_id": None,
                "module_title": None,
                # EP Step
                "step_id": None,
                "step_title": None,
                "step_description": None,
                # Planner sub-step
                "implementation_sub_step_id": None,
                "implementation_sub_step_title": None,
                "implementation_sub_step_description": None,
                "implementation_sub_step_required_assets": None,
                "implementation_sub_step_required_template": None,
                # Executor
                "generated_code_id": 0,
                "generated_code": None,
                # Validator
                "validation_id": 0,
                "validation_status": None,
                "validation_vector": None,
                "validation_checks": None,
                "validation_reasoning": None,
            },
        "dataset": [],
        "history": [],
        "errors": [],
    }
    
    if debug:
        print(f"\n{'='*70}")
        print(f"Starting workflow execution.")
        print(f"{'='*70}\n")
    
    config = GraphConfig.from_env()
    final_state = workflow.invoke(initial_state, {"recursion_limit": config.recursion_limit})
    
    if debug:
        print(f"\n{'='*70}")
        print("Workflow History:")
        print(f"{'='*70}")
        for event in final_state.get("history", []):
            print(f"  • {event}")
        
        if final_state.get("errors"):
            print(f"\n{'='*70}")
            print("Errors:")
            print(f"{'='*70}")
            for error in final_state["errors"]:
                print(f"  ✗ {error}")
    
    return final_state


__all__ = [
    "WorkflowState",
    "build_workflow_graph",
    "run_workflow",
]
