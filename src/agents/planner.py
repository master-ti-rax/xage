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

from src.utils.saving import save_agent_output
from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.planner_prompts import (
    PLANNER_HIERARCHY_SYSTEM_PROMPT,
    PLANNER_HIERARCHY_INPUT_PROMPT,
    PLANNER_DECOMPOSE_SYSTEM_PROMPT,
    PLANNER_DECOMPOSE_INPUT_PROMPT,
    PLANNER_TEMPLATES_SYSTEM_PROMPT,
    PLANNER_TEMPLATES_INPUT_PROMPT,
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

        save_agent_output(
            agent_name=f"{self.name}_hierarchy_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
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

        save_agent_output(
            agent_name=f"{self.name}_hierarchy",
            content=result,
            extension=".txt",
            mode="raw",
        )

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
    ) -> list[dict[str, Any]]:
        """Decompose a module into ≤5 atomic implementation steps.

        Args:
            module_brief: JSON string of the module brief.
            scene_hierarchy: The scene hierarchy from Duty 1.

        Returns:
            List of step dicts, each with step_id, title, what, why,
            scene_objects_involved.
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

        save_agent_output(
            agent_name=f"{self.name}_decompose_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
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

        save_agent_output(
            agent_name=f"{self.name}_decompose",
            content=result,
            extension=".txt",
            mode="raw",
        )

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "steps" in parsed:
            return parsed["steps"]

        logger.warning("Failed to parse steps from LLM output, using fallback")
        return self._fallback_steps(module_brief)

    # -----------------------------------------------------------------
    # Duty 3: Template Strategy & Resource Specification
    # -----------------------------------------------------------------

    def select_templates_and_resources(
        self,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Enrich steps with template mappings & required assets/knowledge.

        Args:
            steps: The raw steps from Duty 2.

        Returns:
            Dict with enriched_steps list and new_template_proposals list.
        """
        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(
            templates_structured, include_signatures=True,
        )

        system_prompt = PLANNER_TEMPLATES_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )
        input_text = PLANNER_TEMPLATES_INPUT_PROMPT.format(
            implementation_steps=json.dumps(steps, indent=2),
            available_templates=templates_text if templates_text else "No templates available.",
        )

        save_agent_output(
            agent_name=f"{self.name}_templates_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
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
            logger.exception("LLM invocation failed during template strategy selection")
            return {"enriched_steps": steps, "new_template_proposals": []}

        save_agent_output(
            agent_name=f"{self.name}_templates",
            content=result,
            extension=".txt",
            mode="raw",
        )

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "enriched_steps" in parsed:
            return parsed

        logger.warning(
            "Failed to parse template enrichment from LLM output; "
            "returning steps without enrichment"
        )
        return {"enriched_steps": steps, "new_template_proposals": []}

    # -----------------------------------------------------------------
    # Orchestration: run all three duties and merge
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

        # ── Duty 2: Step Decomposition ──
        print("  📐 Duty 2: Decomposing into ≤5 Steps...")
        steps = self.decompose_steps(
            module_brief=module_description,
            scene_hierarchy=scene_hierarchy,
        )
        logger.info("Step decomposition: %d steps produced", len(steps))

        # ── Duty 3: Template Strategy + Resources ──
        print("  🔧 Duty 3: Selecting Templates & Resources...")
        enrichment = self.select_templates_and_resources(steps)
        enriched_steps = enrichment.get("enriched_steps", steps)
        new_proposals = enrichment.get("new_template_proposals", [])
        logger.info(
            "Template enrichment: %d enriched steps, %d new proposals",
            len(enriched_steps),
            len(new_proposals),
        )

        # ── Merge into a single plan dict ──
        merged_steps = self._merge_steps(steps, enriched_steps)

        overview = (
            f"Execution plan for scene '{scene_hierarchy.get('scene_root', 'Unknown')}' "
            f"with {len(merged_steps)} implementation steps."
        )

        execution_plan = {
            "overview": overview,
            "scene_hierarchy": scene_hierarchy,
            "implementation_steps": merged_steps,
            "new_template_proposals": new_proposals,
        }

        save_agent_output("planner_execution_plan", execution_plan)
        return execution_plan

    # -----------------------------------------------------------------
    # Merge helper
    # -----------------------------------------------------------------

    @staticmethod
    def _merge_steps(
        raw_steps: list[dict[str, Any]],
        enriched_steps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge raw steps with their enrichment data.

        Enriched steps may only contain step_id + enrichment fields.
        This method overlays the enrichment onto the raw step data.

        Returns:
            The merged list (same length as raw_steps).
        """
        enrichment_map: dict[int, dict[str, Any]] = {}
        for est in enriched_steps:
            sid = est.get("step_id")
            if sid is not None:
                enrichment_map[sid] = est

        merged: list[dict[str, Any]] = []
        for step in raw_steps:
            sid = step.get("step_id")
            edata = enrichment_map.get(sid, {})

            merged_step = dict(step)  # copy base step
            # Overlay enrichment keys that are missing in the base step
            for key in ("template_mapping", "required_assets", "required_knowledge"):
                if key in edata and key not in merged_step:
                    merged_step[key] = edata[key]
                elif key in edata:
                    # If base already had the key, prefer the enriched version
                    merged_step[key] = edata[key]

            merged.append(merged_step)

        return merged

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

        save_agent_output(
            agent_name=f"{self.name}_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
        )

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

        save_agent_output(
            agent_name=self.name,
            content=result,
            extension=".txt",
            mode="raw",
        )

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
