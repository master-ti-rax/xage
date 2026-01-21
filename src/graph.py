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
from src.utils.saving import save_agent_output


# ============================================================================
# Logging Utilities
# ============================================================================

def log_node_start(node_name: str, state: dict[str, Any]) -> None:
    """Log when a node starts executing."""
    current_task = state.get("current_task")
    task_id = current_task.get("task_id") if current_task else "None"
    print(f"\n{'─'*70}")
    print(f"→ NODE: {node_name:20} [Task: {task_id}]")
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
    """Log the raw agent response and wait for user input to continue.
    
    This function displays the complete, unprocessed output from an agent
    and pauses execution until the user presses a key.
    
    Args:
        agent_name: Name of the agent producing the output.
        output: The raw output from the agent (any type).
    """
    print(f"\n{'='*70}")
    print(f"🔍 RAW OUTPUT FROM: {agent_name}")
    print(f"{'='*70}")
    print(f"Type: {type(output).__name__}")
    print(f"{'─'*70}")

    print(output)
    
    print(f"{'─'*70}")
    print(f"📏 Length: {len(str(output))} characters")
    print(f"{'='*70}")
    
    # Wait for user input
    try:
        #input("\n⏸️  Press ENTER to continue...")
        pass
    except EOFError:
        # Handle case where input() is not available (e.g., non-interactive mode)
        pass
    print()


# ============================================================================
# State Schema
# ============================================================================

class WorkflowState(TypedDict, total=False):
    """State schema for the multi-agent workflow."""
    
    goal: str
    educational_plan: dict[str, Any]
    completed_tasks: list[str]
    current_activity: dict[str, Any] | None
    current_task: dict[str, Any] | None
    asset_info: dict[str, Any] | None
    execution_plan: str | None
    execution_plan_dict: dict[str, Any] | None
    current_step_index: int | None
    current_implementation_step: dict[str, Any] | None
    asset_request: dict[str, Any] | None
    retrieved_assets: dict[str, Any] | None
    executor_payload: dict[str, Any] | None
    generated_code: str | None
    generated_file_path: str | None
    validation_result: dict[str, Any] | None
    history: list[str]
    errors: list[str]


# ============================================================================
# Agent Instances
# ============================================================================

def _init_agents(llm_config: LLMConfig | None = None) -> dict[str, Any]:
    """Initialize all agents with optional LLM config."""
    return {
        "orchestrator": OrchestratorAgent(llm_config=LLMConfig(model=os.getenv("ORCHESTRATOR_MODEL"))),
        "asset_manager": AssetManager(),
        "planner": PlannerAgent(llm_config=LLMConfig(model=os.getenv("PLANNER_MODEL"))),
        "executor": ExecutorAgent(llm_config=LLMConfig(model=os.getenv("EXECUTOR_MODEL"))),
        "validator": ValidatorAgent(llm_config=LLMConfig(model=os.getenv("VALIDATOR_MODEL"))),
    }


# ============================================================================
# Node Functions
# ============================================================================

def orchestrator_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Orchestrator Node: Determine the next task from the Educational Plan.
    
    Reads the current project state and identifies the first incomplete task.
    """
    log_node_start("Orchestrator", state)
    
    orchestrator = agents["orchestrator"]
    completed_tasks = state.get("completed_tasks", [])
    
    # Get next task
    result = orchestrator.get_next_task(
        educational_plan=state["educational_plan"],
        completed_tasks=completed_tasks,
    )
    log_raw_agent_response("Orchestrator", result)
    log_agent_output("Orchestrator", result)
    save_agent_output("orchestrator", result)
    
    # Parse result - expecting JSON with task_id and description
    task_info = {"task_id":1, "description": result}
    history = state.get("history", [])
    task_id = task_info.get('task_id', 'UNKNOWN')
    
    # Check if all tasks are complete
    if task_id == "ALL_TASKS_COMPLETE":
        history.append("Orchestrator found all tasks complete")
        return {
            "current_task": None,
            "history": history,
        }
    
    # Safeguard: if task is already in completed list, something is wrong - mark as complete
    if task_id in completed_tasks:
        history.append(f"Orchestrator found task already completed")
        return {
            "current_task": None,
            "history": history,
        }
    
    history.append("Orchestrator returned the educational task")
    return {
        "current_task": task_info,
        "history": history,
    }


def planner_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Planner Node: Coordinate execution steps and required assets."""
    log_node_start("Planner", state)

    if not state.get("current_task"):
        return {}

    planner = agents["planner"]
    history = state.get("history", [])
    last_event = history[-1] if history else ""

    # Case 1: New Task from Orchestrator -> Create Plan
    if last_event == "Orchestrator returned the educational task":
        task_description = state["current_task"].get("description", "")
        
        execution_plan_dict = planner.create_execution_plan(
            task_description=task_description
        )

        execution_plan_json = json.dumps(execution_plan_dict, indent=2)
        log_raw_agent_response("Planner", execution_plan_json)

        num_tasks = len(execution_plan_dict.get("implementation_tasks", []))
        overview = execution_plan_dict.get("overview", "No overview")
        log_agent_output("Planner", f"Plan Overview: {overview}\nTasks: {num_tasks}")
        save_agent_output("planner", execution_plan_dict)

        implementation_steps = execution_plan_dict.get("implementation_steps", [])
        if not implementation_steps:
            history.append("Planner generated an empty execution plan")
            return {
                "execution_plan": execution_plan_json,
                "execution_plan_dict": execution_plan_dict,
                "history": history,
            }

        current_step_index = 0
        current_step = implementation_steps[current_step_index]
        asset_request = {
            "required_assets": current_step.get("required_assets"),
            "required_knowledge": current_step.get("required_knowledge"),
        }

        history.append("Planner requested assets from Asset Manager")

        return {
            "execution_plan": execution_plan_json,
            "execution_plan_dict": execution_plan_dict,
            "current_step_index": current_step_index,
            "current_implementation_step": current_step,
            "asset_request": asset_request,
            "history": history,
        }

    # Case 2: Assets Returned -> Send to Executor
    elif last_event == "Asset Manager returned resources to Planner":
        retrieved_assets = state.get("retrieved_assets")
        current_step = state.get("current_implementation_step")
        current_step_index = state.get("current_step_index")
        
        if current_step is not None:
            executor_payload = {
                "implementation_step": current_step,
                "retrieved_assets": retrieved_assets,
                "step_index": current_step_index,
            }

            log_agent_output(
                "Planner",
                "Prepared implementation step with retrieved assets for Executor",
            )

            history.append("Planner sent implementation step to Executor")

            return {
                "executor_payload": executor_payload,
                "retrieved_assets": None,
                "asset_request": None,
                "history": history,
            }

    # Case 3: Executor Confirmed Completion -> Next Step
    elif last_event == "Executor confirmed implementation completion":
        current_step_index = state.get("current_step_index", 0)
        execution_plan_dict = state.get("execution_plan_dict")
        implementation_steps = execution_plan_dict.get("implementation_steps", [])
        
        next_index = current_step_index + 1
        
        if next_index >= len(implementation_steps):
            # All steps completed for this task
            history.append("Planner determined all implementation steps are complete")
            return {
                "current_task": None, # Signal completion
                "validation_result": None,
                "executor_payload": None,
                "history": history
            }
        
        # Prepare next step
        current_step = implementation_steps[next_index]
        asset_request = {
            "required_assets": current_step.get("required_assets"),
            "required_knowledge": current_step.get("required_knowledge"),
        }
        
        history.append(f"Planner moving to step {next_index + 1}")
        history.append("Planner requested assets from Asset Manager")
        
        return {
            "current_step_index": next_index,
            "current_implementation_step": current_step,
            "asset_request": asset_request,
            "validation_result": None, # Clear so we don't loop
            "executor_payload": None, # Clear previous payload
            "history": history
        }

    return {}


def asset_manager_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Asset Manager Node: Retrieve required knowledge and 3D models.

    Receives a concise asset request from the Planner and fulfills it using
    the available retrieval tools.
    """
    log_node_start("Asset Manager", state)

    asset_request = state.get("asset_request")
    if not asset_request:
        return {}

    asset_manager = agents["asset_manager"]
    required_assets = asset_request.get("required_assets") or []
    required_knowledge = asset_request.get("required_knowledge") or []
    
    # Ensure we have lists (handle None or wrong types)
    if not isinstance(required_assets, list):
        print("Error: required_assets is not a list:")
        print(required_assets)
        required_assets = []
    if not isinstance(required_knowledge, list):
        print("Error: required_knowledge is not a list:")
        print(required_knowledge)
        required_knowledge = []

    # Retrieve assets using tools
    retrieved_assets = asset_manager.retrieve(
        assets=required_assets,
        knowledge=required_knowledge
    )
        
    #retrieved_json = json.dumps(retrieved_assets, indent=2)
    log_raw_agent_response("Asset Manager", retrieved_assets)
    save_agent_output("asset_manager", retrieved_assets)
    
    # Create human-readable summary
    num_knowledge = len(retrieved_assets.get("retrieved_knowledge", []))
    num_models = len(retrieved_assets.get("retrieved_models", []))
    summary = retrieved_assets.get("summary", "Resources retrieved")
    log_agent_output("Asset Manager", f"{summary}\nKnowledge items: {num_knowledge}, Model searches: {num_models}")
    
    history = state.get("history", [])
    history.append("Asset Manager returned resources to Planner")

    
    return {
        "retrieved_assets": retrieved_assets,
        "history": history,
    }


def executor_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Executor Node: Modify C# Unity code based on planner instructions.

    Consumes the implementation payload prepared by the Planner (which already
    bundles the relevant assets) and produces the required code changes.
    """
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
            return {"history": history}
        
        # Failure case - Refinement
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
        # Should not happen given routing, but safe fallback
        return {}

    executor_payload = state.get("executor_payload")
    if not executor_payload:
        return {}
    
    implementation_step = executor_payload.get("implementation_step", {})
    retrieved_assets = executor_payload.get("retrieved_assets")
    
    # Determine existing code
    generated_code = state.get("generated_code")
    if generated_code:
        existing_code = generated_code
    else:
        # Initial template if no code exists yet
        existing_code = """using UnityEngine;
using System.Collections.Generic;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using UnityEngine.XR.Interaction.Toolkit.Interactors;
using Viroo.Interactions.Grab;
using Viroo.Interactions.XRInteractionToolkit;

public class SceneLogic
{
    
    static void CreateScene() 
    {
      // implementation will go here
      
    }
}"""

    # Execute plan and generate code (with retrieved assets context)
    raw_generated_code = executor.implement_step(
        implementation_step=implementation_step,
        existing_code=existing_code,
        retrieved_assets=retrieved_assets,
        validation_feedback=validation_feedback,
    )
    
    # Clean the generated code
    generated_code_str = clean_agent_output(str(raw_generated_code), output_type="csharp")
            
    log_raw_agent_response("Executor", generated_code_str)
    log_agent_output("Executor", generated_code_str)
    save_agent_output("executor", generated_code_str, extension=".cs")
    
    history = state.get("history", [])

    # Check if code was generated
    if not generated_code_str or len(generated_code_str.strip()) < 10:
        history.append("Executor failed to generate valid code")
        print("  ⚠️ Executor failed to generate valid code.")
        return {
            "generated_code": None,
            "generated_file_path": None,
            "history": history,
        }

    # Write to Unity Project
    unity_project_path = os.getenv("UNITY_PROJECT_PATH")
    unity_scripts_path = os.getenv("UNITY_SCRIPTS_PATH")
    generated_file_path = None
    
    if unity_scripts_path:
        try:
             # Resolve path relative to workspace root if it's relative
            if not os.path.isabs(unity_scripts_path):
                unity_scripts_path = os.path.abspath(unity_scripts_path)
            
            scripts_dir = Path(unity_scripts_path)
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Use a fixed name or derive from task
            # For now, let's use SceneLogic.cs as it matches the class name in the prompt
            target_file = scripts_dir / "SceneLogic.cs"
            
            target_file.write_text(generated_code_str, encoding="utf-8")
            generated_file_path = str(target_file)
            print(f"  ✓ Code written to: {generated_file_path}")
            
        except Exception as e:
            print(f"  ⚠️ Failed to write code to Unity project: {e}")
    elif unity_project_path:
        try:
            # Resolve path relative to workspace root if it's relative
            # Assuming workspace root is current working directory
            if not os.path.isabs(unity_project_path):
                unity_project_path = os.path.abspath(unity_project_path)
                
            scripts_dir = Path(unity_project_path) / "Assets" / "Scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Use a fixed name or derive from task
            # For now, let's use SceneLogic.cs as it matches the class name in the prompt
            target_file = scripts_dir / "SceneLogic.cs"
            
            target_file.write_text(generated_code_str, encoding="utf-8")
            generated_file_path = str(target_file)
            print(f"  ✓ Code written to: {generated_file_path}")
            
        except Exception as e:
            print(f"  ⚠️ Failed to write code to Unity project: {e}")
    else:
        print("  ⚠️ UNITY_PROJECT_PATH or UNITY_SCRIPTS_PATH not set, skipping file write.")
    
    history = state.get("history", [])
    history.append("Executor generated code for the implementation step")
    
    return {
        "generated_code": generated_code_str,
        "generated_file_path": generated_file_path,
        "history": history,
    }


def validator_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Validator Node: QA test the completed task in the Unity scene.
    
    Formulates and executes a test plan to verify the task was completed correctly.
    """
    log_node_start("Validator", state)
    
    if not state.get("current_task"):
        return {}
    
    validator = agents["validator"]
#    task_description = state["current_task"].get("description", "")
    generated_code = state.get("generated_code", "")
    generated_file_path = state.get("generated_file_path")
    
    # Retrieve assets from executor payload if available
    executor_payload = state.get("executor_payload", {})
    retrieved_assets = executor_payload.get("retrieved_assets")
    implementation_step = executor_payload.get("implementation_step")
    
    # Validate task
    validation_result = validator.validate_implementation_step(
        generated_code=generated_code,
        retrieved_assets=retrieved_assets,
        file_path=generated_file_path,
        implementation_step=implementation_step,
    )
    log_raw_agent_response("Validator", validation_result)
    log_agent_output("Validator", validation_result)
    save_agent_output("validator", validation_result)
    
    history = state.get("history", [])
    history.append(
        f"Validator completed validation: "
        f"{validation_result.get('validation_status', 'Unknown')}"
    )
    history.append("Validator reported validation result to Executor")
    
    return {
        "validation_result": validation_result,
        "history": history,
    }


# ============================================================================
# Conditional Routing Functions
# ============================================================================

def route(state: dict[str, Any]) -> str:
    """Determine the next node using the latest entry recorded in history."""
    history = state.get("history") or []
    last_event = history[-1] if history else ""

    routing_rules = [
        ("Orchestrator returned the educational task", "planner"),
        ("Orchestrator found all tasks complete", "end"),
        ("Orchestrator found task already completed", "end"),
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

    # if state.get("current_task") is None:
    #     return "end"
    return "end"


def finalize_task_node(state: dict[str, Any], agents: dict[str, Any]) -> dict[str, Any]:
    """Finalize a successfully completed task."""
    log_node_start("Finalize Task", state)
    
    task_id = state.get("current_task", {}).get("task_id", "")
    completed_tasks = state.get("completed_tasks", [])
    if task_id and task_id not in completed_tasks:
        completed_tasks.append(task_id)
    
    print(f"  ✓ Task {task_id} marked as complete")
    
    history = state.get("history", [])
    
    return {
        "completed_tasks": completed_tasks,
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
    """Build and compile the LangGraph workflow.
    
    Args:
        llm_config: Optional LLM configuration for all agents.
    
    Returns:
        Compiled LangGraph StateGraph ready for execution.
    """
    agents = _init_agents(llm_config)
    
    # Create state graph with TypedDict schema
    graph = StateGraph(WorkflowState)
    
    # Add nodes (partial functions to pass agents)
    graph.add_node(
        "orchestrator",
        lambda state: orchestrator_node(state, agents),
    )
    graph.add_node(
        "asset_manager",
        lambda state: asset_manager_node(state, agents),
    )
    graph.add_node(
        "planner",
        lambda state: planner_node(state, agents),
    )
    graph.add_node(
        "executor",
        lambda state: executor_node(state, agents),
    )
    graph.add_node(
        "validator",
        lambda state: validator_node(state, agents),
    )
    
    # Add edges
    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        route,
        {
            "planner": "planner",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "planner",
        route,
        {
            "asset_manager": "asset_manager",
            "executor": "executor",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "asset_manager",
        route,
        {
            "planner": "planner",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "executor",
        route,
        {
            "validator": "validator",
            "planner": "planner",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "validator",
        route,
        {
            "executor": "executor",
            "end": END,
        },
    )


    #graph.add_edge("orchestrator", "validator")
    # graph.add_conditional_edges(
    #     "validator",
    #     is_validation_success,
    #     {
    #         "finalize_task": "finalize_task",
    #         "record_failure": "record_failure",
    #         "orchestrator": "orchestrator",
    #     },
    # )
    # graph.add_edge("finalize_task", "orchestrator")
    # graph.add_edge("record_failure", "orchestrator")
    
    # Compile and return
    return graph.compile()


# ============================================================================
# Execution Interface
# ============================================================================

def run_workflow(
    goal: str,
    educational_plan: dict[str, Any],
    llm_config: LLMConfig | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """Run the complete workflow.
    
    Args:
        goal: High-level goal or description of the project.
        educational_plan: The Educational Plan (EP) as a dict with modules and steps.
        llm_config: Optional LLM configuration.
        debug: If True, print debug information during execution.
    
    Returns:
        Final state after workflow completion.
    """
    # Build workflow
    workflow = build_workflow_graph(llm_config)
    
    # Initialize state
    initial_state = {
        "goal": goal,
        "educational_plan": educational_plan,
        "completed_tasks": [],
        "current_task": None,
        "asset_info": None,
        "execution_plan": None,
        "execution_plan_dict": None,
        "current_step_index": None,
        "current_implementation_step": None,
        "asset_request": None,
        "retrieved_assets": None,
        "executor_payload": None,
        "generated_code": None,
        "validation_result": None,
        "history": [],
        "errors": [],
    }
    
    # Run workflow
    if debug:
        print(f"\n{'='*70}")
        print(f"Starting workflow: {goal}")
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
