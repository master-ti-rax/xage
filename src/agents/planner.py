"""Planner Agent for creating execution plans.

The Planner has three duties:
1. Scene Hierarchy Definition – define the Unity scene graph for a module.
2. Step Decomposition – break the module into ≤5 atomic implementation steps.
3. Template Strategy & Resource Spec – map each step to templates and list
   required assets/knowledge.

The three duties run sequentially and their outputs are merged into a single
Execution Plan dict consumed by the downstream Asset Manager / Executor.
"""

from __future__ import annotations

import logging
import os
import json
from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.planner_prompts import (
    PLANNER_HIERARCHY_SYSTEM_PROMPT,
    PLANNER_HIERARCHY_INPUT_PROMPT,
    PLANNER_DECOMPOSE_SYSTEM_PROMPT,
    PLANNER_DECOMPOSE_INPUT_PROMPT,
)
from src.utils.cleaning import clean_agent_output
from src.utils.templates import get_templates_structured, format_templates_for_agent

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Planner Agent that creates execution plans for the Executor.

    Implements three duties that run in sequence to produce a rich plan:
    - define_scene_hierarchy(): Unity scene graph for the module.
    - decompose_steps(): ≤5 atomic implementation steps.
    - select_templates_and_resources(): Template mappings + asset/knowledge lists.
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
    ) -> None:
        """Initialize the Planner Agent.

        Args:
            llm_config: LLM configuration. If None, uses default from environment.
        """
        self._llm_config = llm_config
        model = BaseModel(config=llm_config).client

        # Get environment context
        self._unity_version = os.getenv("UNITY_VERSION", "2022.3")
        self._xr_framework = os.getenv("UNITY_XR_FRAMEWORK", "XR Interaction Toolkit (XRIT)")

        # Initialize with hierarchy prompt as default; swapped per duty
        formatted_system_prompt = PLANNER_HIERARCHY_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )

        super().__init__(
            name="PlannerAgent",
            model=model,
            system_prompt=formatted_system_prompt,
        )

    # -----------------------------------------------------------------
    # Duty 1: Scene Hierarchy Definition
    # -----------------------------------------------------------------

    def define_scene_hierarchy(
        self,
        module_brief: str,
        running_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Define the Unity scene hierarchy for a module.

        Args:
            module_brief: JSON string of the module brief from the Orchestrator.
            running_context: What has been built so far (running summary).

        Returns:
            Scene hierarchy dict with scene_root and hierarchy tree.
        """
        context_text = json.dumps(running_context, indent=2) if running_context else "{}"

        system_prompt = PLANNER_HIERARCHY_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )
        input_text = PLANNER_HIERARCHY_INPUT_PROMPT.format(
            module_brief=module_brief,
            running_context=context_text,
        )

        state = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ]
        }

        try:
            result = self.invoke(state)
        except Exception:
            logger.exception("LLM invocation failed during scene hierarchy definition")
            return self._fallback_hierarchy(module_brief)

        content = result["messages"][-1].content
        hierarchy = clean_agent_output(content, output_type="json")

        if hierarchy and "hierarchy" in hierarchy:
            return hierarchy

        logger.warning("Failed to parse scene hierarchy from LLM output, using fallback")
        return self._fallback_hierarchy(module_brief)

    # -----------------------------------------------------------------
    # Duty 2: Step Decomposition
    # -----------------------------------------------------------------

    def decompose_steps(
        self,
        module_brief: str,
        scene_hierarchy: dict[str, Any],
    ) -> dict[str, Any]:
        """Decompose a module into ≤5 atomic implementation steps.

        Args:
            module_brief: JSON string of the module brief.
            scene_hierarchy: The scene hierarchy from Duty 1.

        Returns:
            Dict containing steps and new_template_proposals.
        """
        hierarchy_text = json.dumps(scene_hierarchy, indent=2)
        
        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(
            templates_structured, include_signatures=True,
        )

        system_prompt = PLANNER_DECOMPOSE_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )
        input_text = PLANNER_DECOMPOSE_INPUT_PROMPT.format(
            module_brief=module_brief,
            scene_hierarchy=hierarchy_text,
            available_templates=templates_text if templates_text else "No templates available.",
        )

        state = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ]
        }

        try:
            result = self.invoke(state)
        except Exception:
            logger.exception("LLM invocation failed during step decomposition")
            return self._fallback_steps(module_brief)

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "steps" in parsed:
            return parsed

        logger.warning("Failed to parse steps from LLM output, using fallback")
        return {
            "steps": self._fallback_steps(module_brief),
            "new_template_proposals": []
        }

    # -----------------------------------------------------------------
    # Orchestration: run all duties and merge
    # -----------------------------------------------------------------

    def create_execution_plan(
        self,
        module_description: str,
        running_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a full Execution Plan by running all three duties.

        This is the primary entry-point called by the graph's planner_node.

        Args:
            module_description: The module brief (JSON string or plain text).
            running_context: Running summary of what has been built so far.

        Returns:
            Merged Execution Plan dict with:
            - overview, scene_hierarchy, implementation_steps (enriched),
            - new_template_proposals.
        """
        # ── Duty 1: Scene Hierarchy ──
        print("  🏗️  Duty 1: Defining Scene Hierarchy...")
        scene_hierarchy = self.define_scene_hierarchy(
            module_brief=module_description,
            running_context=running_context,
        )
        logger.info(
            "Scene hierarchy defined: root=%s, nodes=%d",
            scene_hierarchy.get("scene_root", "?"),
            len(scene_hierarchy.get("hierarchy", [])),
        )

        # ── Duty 2: Step Decomposition (inc. Templates/Resources) ──
        print("  📐 Duty 2: Decomposing into ≤5 Steps...")
        decompose_res = self.decompose_steps(
            module_brief=module_description,
            scene_hierarchy=scene_hierarchy,
        )
        steps = decompose_res.get("steps", [])
        new_proposals = decompose_res.get("new_template_proposals", [])
        logger.info(
            "Step decomposition: %d steps produced, %d new proposals",
            len(steps),
            len(new_proposals),
        )

        overview = (
            f"Execution plan for scene '{scene_hierarchy.get('scene_root', 'Unknown')}' "
            f"with {len(steps)} implementation steps."
        )

        execution_plan = {
            "overview": overview,
            "scene_hierarchy": scene_hierarchy,
            "implementation_steps": steps,
            "new_template_proposals": new_proposals,
        }

        return execution_plan

    # -----------------------------------------------------------------
    # Fallback helpers (deterministic, no LLM needed)
    # -----------------------------------------------------------------

    @staticmethod
    def _fallback_hierarchy(module_brief: str) -> dict[str, Any]:
        """Build a minimal scene hierarchy when the LLM fails."""
        # Try to extract a title from the module brief
        title = "UnknownModule"
        try:
            brief_dict = json.loads(module_brief)
            title = brief_dict.get("module_title", brief_dict.get("title", title))
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "scene_root": title,
            "hierarchy": [
                {
                    "name": "Environment",
                    "purpose": "Base environment for the training module",
                },
                {
                    "name": "StepContainer",
                    "purpose": "Parent for all training step GameObjects",
                },
            ],
        }

    @staticmethod
    def _fallback_steps(module_brief: str) -> list[dict[str, Any]]:
        """Build a minimal step list when the LLM fails."""
        return [
            {
                "step_id": 0,
                "title": "Scene & Exercise Setup",
                "what": "Create the exercise root and step container.",
                "why": "Initialize the training scenario.",
                "scene_objects_involved": ["ExerciseRoot", "StepContainer"],
            },
            {
                "step_id": 1,
                "title": "Module Implementation",
                "what": f"Implement the module as described: {module_brief[:300]}",
                "why": "Core module functionality.",
                "scene_objects_involved": [],
            },
        ]

    # -----------------------------------------------------------------
    # Legacy method (kept for backward compatibility)
    # -----------------------------------------------------------------

    def create_execution_plan_legacy(
        self,
        task_description: str,
    ) -> dict[str, Any]:
        """Legacy single-shot plan creation.

        Superseded by the three-duty ``create_execution_plan()``.
        Kept for backward compatibility.
        """
        from src.prompts.planner_prompts import (
            PLANNER_SYSTEM_PROMPT,
            PLANNER_INPUT_PROMPT,
        )

        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(
            templates_structured, include_signatures=False,
        )

        input_text = PLANNER_INPUT_PROMPT.format(
            task_description=task_description,
        )
        if templates_text:
            input_text += "\n\n**AVAILABLE TEMPLATES:**\n" + templates_text

        formatted_system = PLANNER_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )

        state = {
            "messages": [
                {"role": "system", "content": formatted_system},
                {"role": "user", "content": input_text},
            ]
        }

        try:
            result = self.invoke(state)
        except Exception:
            logger.exception("Legacy plan creation LLM invocation failed")
            return {
                "overview": "Failed to create plan",
                "implementation_steps": [],
                "new_template_proposals": [],
            }

        content = result["messages"][-1].content
        execution_plan = clean_agent_output(content, output_type="json")

        if execution_plan:
            return execution_plan

        logger.warning("Failed to parse JSON from legacy planner response")
        return {
            "overview": "Failed to parse structured plan",
            "implementation_steps": [],
            "required_knowledge": [],
            "required_assets": [],
            "technical_notes": content,
            "_raw_response": content,
        }
