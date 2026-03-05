"""Tests for agent classes."""

import json
import pytest
from src.agents.orchestrator import OrchestratorAgent
from src.agents.planner import PlannerAgent


# ============================================================================
# OrchestratorAgent Tests
# ============================================================================


class TestOrchestratorAgent:
    """Tests for the refactored OrchestratorAgent (v2 duties)."""

    def test_create_initial_running_summary(self):
        """Test that initial running summary has the expected structure."""
        summary = OrchestratorAgent.create_initial_running_summary()
        assert summary == {
            "objects_in_scene": [],
            "scripts_generated": [],
            "completed_modules": [],
            "notes": [],
        }

    def test_update_running_summary_adds_module(self):
        """Test that update_running_summary tracks completed modules."""
        summary = OrchestratorAgent.create_initial_running_summary()
        updated = OrchestratorAgent.update_running_summary(
            running_summary=summary,
            module_title="Environment Setup",
        )
        assert "Environment Setup" in updated["completed_modules"]

    def test_update_running_summary_tracks_scripts(self):
        """Test that update_running_summary tracks generated scripts."""
        summary = OrchestratorAgent.create_initial_running_summary()
        updated = OrchestratorAgent.update_running_summary(
            running_summary=summary,
            module_title="Module 1",
            generated_file_path="/path/to/SceneLogic.cs",
        )
        assert "/path/to/SceneLogic.cs" in updated["scripts_generated"]

    def test_update_running_summary_extracts_gameobjects(self):
        """Test that update_running_summary extracts GameObject names from code."""
        summary = OrchestratorAgent.create_initial_running_summary()
        code = '''
        GameObject workbench = Spawner.SpawnObject("Workbench");
        GameObject gloves = Template.CreateModule("SafetyGloves");
        '''
        updated = OrchestratorAgent.update_running_summary(
            running_summary=summary,
            module_title="Module 1",
            generated_code=code,
        )
        assert "workbench" in updated["objects_in_scene"]
        assert "gloves" in updated["objects_in_scene"]

    def test_update_running_summary_no_duplicates(self):
        """Test that update_running_summary doesn't duplicate entries."""
        summary = OrchestratorAgent.create_initial_running_summary()
        summary = OrchestratorAgent.update_running_summary(
            running_summary=summary,
            module_title="Module 1",
        )
        summary = OrchestratorAgent.update_running_summary(
            running_summary=summary,
            module_title="Module 1",  # same module again
        )
        assert summary["completed_modules"].count("Module 1") == 1

    def test_fallback_manifest(self):
        """Test the deterministic fallback manifest builder."""
        orch = OrchestratorAgent.__new__(OrchestratorAgent)
        plan = {
            "plans": [{
                "metadata": {"title": "Test Plan", "short_description": "A test."},
                "learning_objectives": ["Learn X"],
                "detailed_learning_design": {
                    "training_script": {
                        "modules": [{"module_id": 1}, {"module_id": 2}]
                    }
                }
            }]
        }
        manifest = orch._fallback_manifest(plan)
        assert manifest["title"] == "Test Plan"
        assert manifest["total_modules"] == 2
        assert "Learn X" in manifest["learning_objectives"]

    def test_fallback_segment(self):
        """Test the deterministic fallback segmentation."""
        orch = OrchestratorAgent.__new__(OrchestratorAgent)
        plan = {
            "plans": [{
                "detailed_learning_design": {
                    "training_script": {
                        "modules": [
                            {
                                "module_id": 1,
                                "title": "Intro",
                                "pedagogical_rationale": "Onboarding.",
                                "learning_outcomes": ["Navigate the scene"],
                                "learning_flow": {
                                    "steps": [
                                        {"title": "Step A", "description": "Do A."}
                                    ]
                                }
                            },
                            {
                                "module_id": 2,
                                "title": "Safety",
                                "pedagogical_rationale": "Safety rules.",
                                "learning_outcomes": ["Understand zones"],
                                "learning_flow": {
                                    "steps": [
                                        {"title": "Step B", "description": "Do B."}
                                    ]
                                }
                            },
                        ]
                    }
                }
            }]
        }
        modules = orch._fallback_segment(plan)
        assert len(modules) == 2
        assert modules[0]["title"] == "Intro"
        assert modules[1]["title"] == "Safety"
        assert modules[0]["depends_on"] == []
        assert modules[1]["depends_on"] == [1]

    def test_segment_plan_deterministic(self):
        """Test deterministic segmentation extracts rich modules from plan JSON."""
        orch = OrchestratorAgent.__new__(OrchestratorAgent)
        plan = {
            "plans": [{
                "detailed_learning_design": {
                    "training_script": {
                        "modules": [
                            {
                                "module_id": 1,
                                "title": "Introduction",
                                "duration_minutes": 25,
                                "pedagogical_rationale": "Onboarding phase.",
                                "learning_outcomes": ["Navigate the scene", "Use controls"],
                                "learning_flow": {
                                    "description": "Sequential steps.",
                                    "steps": [
                                        {"title": "Orientation", "description": "Learn layout."},
                                        {"title": "Movement", "description": "Walk to points."},
                                    ]
                                },
                                "learner_monitoring": ["Time spent", "Errors"],
                            },
                            {
                                "module_id": 2,
                                "title": "Safety",
                                "duration_minutes": 50,
                                "pedagogical_rationale": "Safety awareness.",
                                "learning_outcomes": ["Recognize zones"],
                                "learning_flow": {
                                    "description": "Rule-based steps.",
                                    "steps": [
                                        {"title": "Zone Recognition", "description": "Learn colors."},
                                    ]
                                },
                                "learner_monitoring": ["Violations"],
                            },
                        ]
                    }
                }
            }]
        }
        modules = orch.segment_plan(plan)
        assert len(modules) == 2
        # Check first module has rich fields
        m1 = modules[0]
        assert m1["title"] == "Introduction"
        assert m1["duration_minutes"] == 25
        assert "Navigate the scene" in m1["learning_outcomes"]
        assert m1["depends_on"] == []
        assert "Onboarding phase." in m1["description"]
        assert "Orientation" in m1["description"]
        assert m1["learner_monitoring"] == ["Time spent", "Errors"]
        # Check second module dependencies
        assert modules[1]["depends_on"] == [1]

    def test_segment_plan_no_modules_fallback(self):
        """Test deterministic segmentation with a plan that has no modules."""
        orch = OrchestratorAgent.__new__(OrchestratorAgent)
        plan = {
            "plans": [{
                "metadata": {"title": "Empty Plan", "long_description": "A plan with no modules."},
                "detailed_learning_design": {"training_script": {}}
            }]
        }
        modules = orch.segment_plan(plan)
        assert len(modules) == 1
        assert modules[0]["title"] == "Empty Plan"

    def test_prepare_module_handoff_deterministic(self):
        """Test deterministic handoff assembles a complete Module Brief."""
        orch = OrchestratorAgent.__new__(OrchestratorAgent)
        manifest = {
            "title": "Battery Inspection VR",
            "environment_description": "Industrial recycling facility",
            "learning_objectives": ["Obj1", "Obj2"],
        }
        module = {
            "module_id": 2,
            "title": "Safety Boundaries",
            "description": "Learn about safety zones in robot workspace.",
            "duration_minutes": 50,
            "learning_outcomes": ["Recognize zones", "Interpret warnings"],
            "learner_monitoring": ["Boundary violations", "Reaction time"],
            "depends_on": [1],
        }
        running_summary = {
            "objects_in_scene": ["Workbench"],
            "scripts_generated": ["Intro.cs"],
            "completed_modules": ["Introduction"],
            "notes": [],
        }
        brief = orch.prepare_module_handoff(manifest, module, running_summary)
        assert brief["module_id"] == 2
        assert brief["module_title"] == "Safety Boundaries"
        assert "safety zones" in brief["module_description"].lower()
        assert brief["project_context"]["title"] == "Battery Inspection VR"
        assert "Recognize zones" in brief["project_context"]["learning_objectives_for_module"]
        assert brief["already_built"]["completed_modules"] == ["Introduction"]
        assert "50 minutes" in brief["instructions_for_planner"]
        assert "Boundary violations" in brief["instructions_for_planner"]

    def test_prepare_module_handoff_falls_back_to_manifest_objectives(self):
        """Test handoff falls back to manifest objectives when module has none."""
        orch = OrchestratorAgent.__new__(OrchestratorAgent)
        manifest = {
            "title": "Test",
            "learning_objectives": ["Global Obj"],
        }
        module = {
            "module_id": 1,
            "title": "First Module",
            "description": "Do stuff.",
        }
        running_summary = OrchestratorAgent.create_initial_running_summary()
        brief = orch.prepare_module_handoff(manifest, module, running_summary)
        assert "Global Obj" in brief["project_context"]["learning_objectives_for_module"]


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

    def test_merge_steps_basic(self):
        """Test that raw steps get enrichment overlaid."""
        raw = [
            {"step_id": 0, "title": "Setup", "what": "do X", "why": "because"},
            {"step_id": 1, "title": "Build", "what": "do Y", "why": "because"},
        ]
        enriched = [
            {
                "step_id": 0,
                "template_mapping": [{"file": "A.cs", "function": "Init"}],
                "required_assets": [{"name": "Table", "type": "3D model"}],
                "required_knowledge": [],
            },
            {
                "step_id": 1,
                "template_mapping": [],
                "required_assets": [],
                "required_knowledge": [{"topic": "XR", "description": "docs"}],
            },
        ]

        merged = PlannerAgent._merge_steps(raw, enriched)
        assert len(merged) == 2
        # Step 0 should keep its base fields + gain enrichment
        assert merged[0]["title"] == "Setup"
        assert merged[0]["template_mapping"] == [{"file": "A.cs", "function": "Init"}]
        assert merged[0]["required_assets"] == [{"name": "Table", "type": "3D model"}]
        # Step 1 should gain required_knowledge
        assert merged[1]["required_knowledge"] == [{"topic": "XR", "description": "docs"}]

    def test_merge_steps_enrichment_overwrites(self):
        """Test that enrichment keys overwrite base step data."""
        raw = [
            {
                "step_id": 0,
                "title": "Setup",
                "required_assets": [{"name": "OldAsset", "type": "3D model"}],
            },
        ]
        enriched = [
            {
                "step_id": 0,
                "required_assets": [{"name": "NewAsset", "type": "3D model"}],
            },
        ]
        merged = PlannerAgent._merge_steps(raw, enriched)
        assert merged[0]["required_assets"] == [{"name": "NewAsset", "type": "3D model"}]

    def test_merge_steps_no_enrichment(self):
        """Test that missing enrichment keeps raw steps intact."""
        raw = [
            {"step_id": 0, "title": "Setup", "what": "do X", "why": "because"},
        ]
        merged = PlannerAgent._merge_steps(raw, [])
        assert merged[0] == raw[0]
