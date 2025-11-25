"""Tests for orchestrator tools."""

import json
import pytest

from src.tools.orchestrator_tools import (
    parse_educational_plan,
    get_next_incomplete_task,
    get_plan_progress,
    ParsedEducationalPlan,
)


# Sample Educational Plan for testing
SAMPLE_EP = {
    "title": "VR Chemistry Lab",
    "modules": [
        {
            "id": "module_1",
            "title": "Lab Setup",
            "steps": [
                {
                    "id": "step_1_1",
                    "title": "Create Lab Environment",
                    "description": "Set up the basic VR lab environment with tables and equipment.",
                },
                {
                    "id": "step_1_2",
                    "title": "Add Safety Equipment",
                    "description": "Add goggles, gloves, and fire extinguisher to the lab.",
                },
            ],
        },
        {
            "id": "module_2",
            "title": "Chemistry Experiments",
            "steps": [
                {
                    "id": "step_2_1",
                    "title": "Acid-Base Reaction",
                    "description": "Implement a simple acid-base titration experiment.",
                },
                {
                    "id": "step_2_2",
                    "title": "Combustion Demo",
                    "description": "Create a combustion reaction demonstration.",
                },
            ],
        },
    ],
}


def test_parse_educational_plan():
    """Test parsing an Educational Plan."""
    result_json = parse_educational_plan(SAMPLE_EP)
    result = json.loads(result_json)
    
    assert result["status"] == "success"
    assert result["total_steps"] == 4
    assert len(result["step_ids"]) == 4
    assert "step_1_1" in result["step_ids"]
    assert "step_2_2" in result["step_ids"]


def test_parsed_educational_plan_structure():
    """Test the ParsedEducationalPlan data structure."""
    parsed = ParsedEducationalPlan(raw_plan=SAMPLE_EP)
    
    assert parsed.get_total_steps() == 4
    assert len(parsed.get_all_step_ids()) == 4
    
    # Test get_step_by_id
    step = parsed.get_step_by_id("step_1_2")
    assert step is not None
    assert step.title == "Add Safety Equipment"
    assert step.module_title == "Lab Setup"
    assert step.order_in_module == 1


def test_get_next_incomplete_task_first():
    """Test getting the first task when none are completed."""
    # Parse plan first
    parse_educational_plan(SAMPLE_EP)
    
    # Get next task with no completed tasks
    result_json = get_next_incomplete_task([])
    result = json.loads(result_json)
    
    assert result["status"] == "task_found"
    assert result["task_id"] == "step_1_1"
    assert result["title"] == "Create Lab Environment"
    assert result["module_id"] == "module_1"


def test_get_next_incomplete_task_middle():
    """Test getting a task in the middle of the plan."""
    # Parse plan first
    parse_educational_plan(SAMPLE_EP)
    
    # Get next task with some completed tasks
    completed = ["step_1_1", "step_1_2"]
    result_json = get_next_incomplete_task(completed)
    result = json.loads(result_json)
    
    assert result["status"] == "task_found"
    assert result["task_id"] == "step_2_1"
    assert result["title"] == "Acid-Base Reaction"
    assert result["module_title"] == "Chemistry Experiments"


def test_get_next_incomplete_task_all_complete():
    """Test when all tasks are complete."""
    # Parse plan first
    parse_educational_plan(SAMPLE_EP)
    
    # Get next task with all tasks completed
    completed = ["step_1_1", "step_1_2", "step_2_1", "step_2_2"]
    result_json = get_next_incomplete_task(completed)
    result = json.loads(result_json)
    
    assert result["status"] == "all_complete"
    assert result["task_id"] == "ALL_TASKS_COMPLETE"
    assert result["total_completed"] == 4


def test_get_plan_progress_beginning():
    """Test progress at the beginning."""
    # Parse plan first
    parse_educational_plan(SAMPLE_EP)
    
    result_json = get_plan_progress([])
    result = json.loads(result_json)
    
    assert result["total_steps"] == 4
    assert result["completed"] == 0
    assert result["remaining"] == 4
    assert result["progress_percentage"] == 0.0
    assert result["current_module"] == "Lab Setup"


def test_get_plan_progress_middle():
    """Test progress in the middle."""
    # Parse plan first
    parse_educational_plan(SAMPLE_EP)
    
    completed = ["step_1_1", "step_1_2"]
    result_json = get_plan_progress(completed)
    result = json.loads(result_json)
    
    assert result["total_steps"] == 4
    assert result["completed"] == 2
    assert result["remaining"] == 2
    assert result["progress_percentage"] == 50.0
    assert result["current_module"] == "Chemistry Experiments"


def test_get_plan_progress_complete():
    """Test progress when complete."""
    # Parse plan first
    parse_educational_plan(SAMPLE_EP)
    
    completed = ["step_1_1", "step_1_2", "step_2_1", "step_2_2"]
    result_json = get_plan_progress(completed)
    result = json.loads(result_json)
    
    assert result["total_steps"] == 4
    assert result["completed"] == 4
    assert result["remaining"] == 0
    assert result["progress_percentage"] == 100.0
    assert result["current_module"] == "All Complete"


def test_sequential_task_execution():
    """Test a complete sequential execution flow."""
    # Parse plan
    parse_result = json.loads(parse_educational_plan(SAMPLE_EP))
    assert parse_result["status"] == "success"
    
    completed = []
    expected_order = ["step_1_1", "step_1_2", "step_2_1", "step_2_2"]
    
    for expected_id in expected_order:
        # Get next task
        task_result = json.loads(get_next_incomplete_task(completed))
        assert task_result["status"] == "task_found"
        assert task_result["task_id"] == expected_id
        
        # Mark as completed
        completed.append(expected_id)
    
    # After all tasks, should be complete
    final_result = json.loads(get_next_incomplete_task(completed))
    assert final_result["status"] == "all_complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
