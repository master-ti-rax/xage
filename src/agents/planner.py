"""Planner Agent for creating execution plans.

The Planner has two duties:
1. Scene Hierarchy Definition – define the Unity scene graph for a module.
2. Step-by-step Decomposition – iterate through each training step inside the
   module (from learning_flow.steps) and decompose each one into ≤5 atomic
   implementation sub-steps with required assets/knowledge.

The duties run sequentially and their outputs are merged into a single
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
    PLANNER_SYSTEM_PROMPT,
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

    Implements two duties that run in sequence to produce a rich plan:
    - define_scene_hierarchy(): Unity scene graph for the module.
    - decompose_step(): ≤5 atomic implementation sub-steps per training step.
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
        formatted_system_prompt = PLANNER_SYSTEM_PROMPT.format(
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

    def decompose_step(
        self,
        step_brief: dict[str, Any],
        module_context: str,
        current_implementation_steps: list[str] | None = None,
    ) -> dict[str, Any]:
        """Decompose a single training step into ≤5 atomic implementation sub-steps.

        Args:
            step_brief: A single step dict from the module's learning_flow.
            module_context: JSON string of the full module brief for context.
            current_implementation_steps: Titles of implementation steps already created.

        Returns:
            Dict containing steps and new_template_proposals for this step.
        """
        #hierarchy_text = json.dumps(scene_hierarchy, indent=2)
        step_brief_text = json.dumps(step_brief, indent=2)

        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(
            templates_structured, include_signatures=False,
        )

        # Format current implementation titles
        if current_implementation_steps:
            current_titles_text = "\n".join(
                f"  - {step}" for step in current_implementation_steps
            )
        else:
            current_titles_text = "None — this is the first step."

        system_prompt = PLANNER_DECOMPOSE_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )
        input_text = PLANNER_DECOMPOSE_INPUT_PROMPT.format(
            step_brief=step_brief_text,
            module_context=module_context,
            current_implementation_steps=current_titles_text,
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
            logger.exception(
                "LLM invocation failed during step decomposition for step %s",
                step_brief.get("step_id", "?"),
            )
            return {
                "steps": self._fallback_steps(json.dumps(step_brief)),
                "new_template_proposals": [],
            }

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "steps" in parsed:
            return parsed

        logger.warning("Failed to parse steps from LLM output, using fallback")
        return {
            "steps": self._fallback_steps(json.dumps(step_brief)),
            "new_template_proposals": []
        }

    # -----------------------------------------------------------------
    # Orchestration: run all duties and merge
    # -----------------------------------------------------------------

    @staticmethod
    def _extract_module_steps(module_description: str) -> list[dict[str, Any]]:
        """Extract training steps from the module's learning_flow.

        Parses the module description (JSON string or plain text) and returns
        the list of steps defined in learning_flow.steps. Returns an empty
        list if the structure is missing or unparseable.
        """
        try:
            brief = json.loads(module_description) if isinstance(module_description, str) else module_description
        except (json.JSONDecodeError, TypeError):
            return []

        if not isinstance(brief, dict):
            return []

        # Steps may be nested in module_data.learning_flow.steps or
        # directly in learning_flow.steps depending on handoff structure.
        for root in (brief.get("module_data", {}), brief):
            if not isinstance(root, dict):
                continue
            learning_flow = root.get("learning_flow")
            if isinstance(learning_flow, dict):
                steps = learning_flow.get("steps")
                if isinstance(steps, list) and steps:
                    return steps

        return []

    def create_execution_plan(
        self,
        module_description: str,
        running_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a full Execution Plan by running all duties.

        This is the primary entry-point called by the graph's planner_node.

        The planner iterates through each training step inside the module
        (from learning_flow.steps) and decomposes them one by one.

        Args:
            module_description: The module brief (JSON string or plain text).
            running_context: Running summary of what has been built so far.

        Returns:
            Merged Execution Plan dict with:
            - overview, scene_hierarchy, implementation_steps (enriched),
            - new_template_proposals.
        """
        # ── Duty 1: Scene Hierarchy ──
        """
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
        """
        # ── Duty 2: Step-by-step Decomposition ──
        module_steps = self._extract_module_steps(module_description)

        # Extract pedagogical_rationale for use as module context in decomposition
        try:
            brief = json.loads(module_description) if isinstance(module_description, str) else module_description
            pedagogical_rationale = (
                brief.get("pedagogical_rationale")
                or brief.get("module_data", {}).get("pedagogical_rationale")
                or module_description
            )
            module_context = (
                json.dumps(pedagogical_rationale, indent=2)
                if not isinstance(pedagogical_rationale, str)
                else pedagogical_rationale
            )
        except (json.JSONDecodeError, TypeError):
            module_context = module_description

        all_impl_steps: list[dict[str, Any]] = []
        all_proposals: list[dict[str, Any]] = []
        completed_steps: list[dict[str, Any]] = []

        if module_steps:
            # Iterate through each training step in the module
            for idx, step in enumerate(module_steps):
                step_label = step.get("step_id")
                print(f"  📐 Duty 2: Decomposing step {idx + 1}/{len(module_steps)}: {step_label}...")

                # Extract titles from already decomposed implementation steps
                current_step_titles = [s.get("title", f"Step {s.get('step_id')}") for s in all_impl_steps]

                decompose_res = self.decompose_step(
                    step_brief=step,
                    module_context=module_context,
                    current_implementation_steps=current_step_titles if current_step_titles else None,
                )

                sub_steps = decompose_res.get("steps", [])
                proposals = decompose_res.get("new_template_proposals", [])

                # Re-number step_ids to be globally unique across the module
                for sub_step in sub_steps:
                    sub_step["step_id"] = len(all_impl_steps)
                    sub_step["parent_step"] = step.get("step_id", f"step_{idx + 1}")
                    sub_step["parent_step_title"] = step.get("title")         
                    sub_step["parent_step_description"] = step.get("description")
                    all_impl_steps.append(sub_step)

                all_proposals.extend(proposals)
                completed_steps.append({
                    "step": step,
                    "implementation_sub_steps": sub_steps,
                })

                logger.info(
                    "Step '%s' decomposed into %d sub-steps",
                    step_label,
                    len(sub_steps),
                )
        else:
            # Fallback: no steps found in learning_flow, decompose module as a whole
            logger.warning("No training steps found in module learning_flow, using fallback decomposition")
            print("  📐 Duty 2: No training steps found — decomposing module as a whole...")
            all_impl_steps = self._fallback_steps(module_description)

        logger.info(
            "Step decomposition complete: %d total implementation steps, %d new proposals",
            len(all_impl_steps),
            len(all_proposals),
        )

        overview = (
            f"Execution plan for module '{module_description}' with {len(module_steps)} training steps, "
            f"with {len(all_impl_steps)} implementation steps."
        )

        execution_plan = {
            "overview": overview,
            #"scene_hierarchy": scene_hierarchy,
            "implementation_steps": all_impl_steps,
            "new_template_proposals": all_proposals,
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


