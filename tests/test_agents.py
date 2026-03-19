"""Tests for agent classes."""

import json
import pytest
from src.agents.planner import PlannerAgent


# ============================================================================
# PlannerAgent Tests
# ============================================================================


class TestPlannerAgent:
    """Tests for the PlannerAgent v2 duties (static / fallback methods)."""

    def test_fallback_hierarchy_with_valid_json(self):
        """Test fallback hierarchy extraction from JSON module brief."""
        brief = json.dumps({"module_title": "Battery Inspection Training"})
        hierarchy = PlannerAgent._fallback_hierarchy(brief)

        assert hierarchy["scene_root"] == "Battery Inspection Training"
        assert len(hierarchy["hierarchy"]) == 2
        names = [node["name"] for node in hierarchy["hierarchy"]]
        assert "Environment" in names
        assert "StepContainer" in names

    def test_fallback_hierarchy_with_plain_text(self):
        """Test fallback hierarchy when module brief is plain text."""
        hierarchy = PlannerAgent._fallback_hierarchy("Some plain text description")

        assert hierarchy["scene_root"] == "UnknownModule"
        assert len(hierarchy["hierarchy"]) == 2

    def test_fallback_steps(self):
        """Test fallback steps always returns at least 2 steps."""
        steps = PlannerAgent._fallback_steps("Implement battery sorting")

        assert len(steps) == 2
        assert steps[0]["step_id"] == 0
        assert steps[0]["title"] == "Scene & Exercise Setup"
        assert steps[1]["step_id"] == 1
        assert "battery sorting" in steps[1]["what"].lower()

