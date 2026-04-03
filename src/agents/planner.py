"""Planner Agent for creating execution plans.

The Planner runs three layered duties that produce a structured Execution Plan
consumed by the downstream Asset Manager / Executor.

Layer 1 – Global Setup (once per XAGE session)
    plan_global_setup(): Instantiate scenery, Exercise Wrapper, Module List
    Wrapper (MultiProcessStep).

Layer 2 – Module Setup (once per module)
    plan_module_setup(): Create Module Wrapper (ProcessStep), add it to the
    Modules List (MultipleProcessStep).

Layer 3 – Per-Step Tasks (once per training step)
    plan_step_tasks(): For each step – instantiate visible objects, add
    exercise module logic, bind logic events, add exercise evaluation.

All three layers are merged inside create_execution_plan() into a single
Execution Plan dict. The dict contains both the structured 3-layer breakdown
(under "layers") and a flat ordered "implementation_steps" list ready for the
graph to iterate.
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
    PLANNER_GLOBAL_SETUP_SYSTEM_PROMPT,
    PLANNER_GLOBAL_SETUP_INPUT_PROMPT,
    PLANNER_MODULE_SETUP_SYSTEM_PROMPT,
    PLANNER_MODULE_SETUP_INPUT_PROMPT,
    PLANNER_SUBDTY_INSTANTIATE_SYSTEM_PROMPT,
    PLANNER_SUBDTY_INSTANTIATE_INPUT_PROMPT,
    PLANNER_SUBDTY_LOGIC_SYSTEM_PROMPT,
    PLANNER_SUBDTY_LOGIC_INPUT_PROMPT,
    PLANNER_SUBDTY_EVENTS_SYSTEM_PROMPT,
    PLANNER_SUBDTY_EVENTS_INPUT_PROMPT,
    PLANNER_SUBDTY_EVALUATION_SYSTEM_PROMPT,
    PLANNER_SUBDTY_EVALUATION_INPUT_PROMPT,
)
from src.utils.cleaning import clean_agent_output
from src.utils.templates import get_templates_structured, format_templates_for_agent

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Planner Agent that creates a 3-layer Execution Plan for the Executor.

    Layer 1 – plan_global_setup(): one-time scene setup tasks.
    Layer 2 – plan_module_setup(): per-module scaffolding tasks.
    Layer 3 – plan_step_tasks(): four ordered sub-duty tasks per training step.
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self._llm_config = llm_config
        model = BaseModel(config=llm_config).client

        self._unity_version = os.getenv("UNITY_VERSION", "2022.3")
        self._xr_framework = os.getenv("UNITY_XR_FRAMEWORK", "XR Interaction Toolkit (XRIT)")

        formatted_system_prompt = PLANNER_SYSTEM_PROMPT.format(
            unity_version=self._unity_version,
            xr_framework=self._xr_framework,
        )

        super().__init__(
            name="PlannerAgent",
            model=model,
            system_prompt=formatted_system_prompt,
        )

    # ------------------------------------------------------------------
    # Layer 1: Global Setup (once per XAGE session)
    # ------------------------------------------------------------------

    def plan_global_setup(self, module_brief: str) -> dict[str, Any]:
        """Plan the one-time global scene setup tasks.

        Args:
            module_brief: JSON string of the module brief (used to infer
                environment-specific assets for the scenery task).

        Returns:
            Dict with key "global_setup_tasks" (list of 3 task dicts).
        """
        system_prompt = PLANNER_GLOBAL_SETUP_SYSTEM_PROMPT
        input_text = PLANNER_GLOBAL_SETUP_INPUT_PROMPT.format(
            module_brief=module_brief,
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
            logger.exception("LLM invocation failed during global setup planning")
            return self._fallback_global_setup()

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "global_setup_tasks" in parsed:
            return parsed

        logger.warning("Failed to parse global setup from LLM output, using fallback")
        return self._fallback_global_setup()

    # ------------------------------------------------------------------
    # Layer 2: Module Setup (once per module)
    # ------------------------------------------------------------------

    def plan_module_setup(self, module_brief: str) -> dict[str, Any]:
        """Plan the per-module scaffolding tasks.

        Args:
            module_brief: JSON string of the module brief.

        Returns:
            Dict with key "module_setup_tasks" (list of 2 task dicts).
        """
        system_prompt = PLANNER_MODULE_SETUP_SYSTEM_PROMPT
        input_text = PLANNER_MODULE_SETUP_INPUT_PROMPT.format(
            module_brief=module_brief,
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
            logger.exception("LLM invocation failed during module setup planning")
            return self._fallback_module_setup(module_brief)

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "module_setup_tasks" in parsed:
            return parsed

        logger.warning("Failed to parse module setup from LLM output, using fallback")
        return self._fallback_module_setup(module_brief)

    # ------------------------------------------------------------------
    # Layer 3: Per-Step Tasks — one LLM call per sub-duty
    # ------------------------------------------------------------------

    def _call_subdty(
        self,
        system_prompt: str,
        input_text: str,
        step_id: Any,
        sub_duty_name: str,
        fallback_task: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke the LLM for a single sub-duty and return the task dict."""
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
                "LLM invocation failed for sub-duty '%s' of step %s",
                sub_duty_name, step_id,
            )
            return fallback_task

        content = result["messages"][-1].content
        parsed = clean_agent_output(content, output_type="json")

        if parsed and "task" in parsed and isinstance(parsed["task"], dict):
            return parsed["task"]

        logger.warning(
            "Failed to parse sub-duty '%s' for step %s, using fallback",
            sub_duty_name, step_id,
        )
        return fallback_task

    def _plan_instantiate(self, step_brief: dict[str, Any], module_context: str, step_id: Any) -> dict[str, Any]:
        step_brief_text = json.dumps(step_brief, indent=2)
        system = PLANNER_SUBDTY_INSTANTIATE_SYSTEM_PROMPT.replace("{step_id}", str(step_id))
        input_text = PLANNER_SUBDTY_INSTANTIATE_INPUT_PROMPT.format(
            step_brief=step_brief_text,
            module_context=module_context,
        )
        return self._call_subdty(
            system, input_text, step_id, "instantiate_visible_objects",
            self._fallback_step_tasks(step_brief)["step_tasks"][0],
        )

    def _plan_logic(self, step_brief: dict[str, Any], module_context: str, step_id: Any) -> dict[str, Any]:
        step_brief_text = json.dumps(step_brief, indent=2)
        templates_text = format_templates_for_agent(
            get_templates_structured(), include_signatures=False,
        ) or "No templates available."
        system = PLANNER_SUBDTY_LOGIC_SYSTEM_PROMPT.replace("{step_id}", str(step_id))
        input_text = PLANNER_SUBDTY_LOGIC_INPUT_PROMPT.format(
            step_brief=step_brief_text,
            module_context=module_context,
            available_templates=templates_text,
        )
        return self._call_subdty(
            system, input_text, step_id, "exercise_module_logic",
            self._fallback_step_tasks(step_brief)["step_tasks"][1],
        )

    def _plan_events(self, step_brief: dict[str, Any], module_context: str, step_id: Any) -> dict[str, Any]:
        step_brief_text = json.dumps(step_brief, indent=2)
        system = PLANNER_SUBDTY_EVENTS_SYSTEM_PROMPT.replace("{step_id}", str(step_id))
        input_text = PLANNER_SUBDTY_EVENTS_INPUT_PROMPT.format(
            step_brief=step_brief_text,
            module_context=module_context,
        )
        return self._call_subdty(
            system, input_text, step_id, "bind_logic_events",
            self._fallback_step_tasks(step_brief)["step_tasks"][2],
        )

    def _plan_evaluation(self, step_brief: dict[str, Any], module_context: str, step_id: Any) -> dict[str, Any]:
        step_brief_text = json.dumps(step_brief, indent=2)
        system = PLANNER_SUBDTY_EVALUATION_SYSTEM_PROMPT.replace("{step_id}", str(step_id))
        input_text = PLANNER_SUBDTY_EVALUATION_INPUT_PROMPT.format(
            step_brief=step_brief_text,
            module_context=module_context,
        )
        return self._call_subdty(
            system, input_text, step_id, "exercise_evaluation",
            self._fallback_step_tasks(step_brief)["step_tasks"][3],
        )

    def plan_step_tasks(
        self,
        step_brief: dict[str, Any],
        module_context: str,
        current_implementation_steps: list[str] | None = None,
    ) -> dict[str, Any]:
        """Plan the four sub-duty tasks for a single training step.

        Makes one focused LLM call per sub-duty to avoid output truncation:
        1. Instantiate visible objects (3D models + Canvas)
        2. Add exercise module logic (steps + parameters)
        3. Bind logic events (StepEventHandlers, UnityEvents, OnClick)
        4. Add exercise evaluation (StepEvaluationHandler, GroupEvaluationHandler)

        Returns:
            Dict with keys "step_tasks" (list of 4 task dicts) and
            "new_template_proposals" (always empty — proposals collected per call).
        """
        step_id = step_brief.get("step_id", "?")

        task_instantiate = self._plan_instantiate(step_brief, module_context, step_id)
        task_logic = self._plan_logic(step_brief, module_context, step_id)
        task_events = self._plan_events(step_brief, module_context, step_id)
        task_evaluation = self._plan_evaluation(step_brief, module_context, step_id)

        return {
            "step_tasks": [task_instantiate, task_logic, task_events, task_evaluation],
            "new_template_proposals": [],
        }

    # ------------------------------------------------------------------
    # Orchestration: run all duties and build the Execution Plan
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_module_steps(module_description: str) -> list[dict[str, Any]]:
        """Extract training steps from the module's learning_flow."""
        try:
            brief = (
                json.loads(module_description)
                if isinstance(module_description, str)
                else module_description
            )
        except (json.JSONDecodeError, TypeError):
            return []

        if not isinstance(brief, dict):
            return []

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
        include_global_setup: bool = True,
    ) -> dict[str, Any]:
        """Create a full 3-layer Execution Plan.

        This is the primary entry-point called by the graph's planner_node.

        Args:
            module_description: The module brief (JSON string or plain text).
            running_context: Running summary of what has been built so far.
            include_global_setup: If False, Layer 1 tasks are omitted from
                implementation_steps (used when global setup was already done
                in a previous module).

        Returns:
            Execution Plan dict with:
            - "overview": human-readable summary string.
            - "layers": structured 3-layer breakdown.
            - "implementation_steps": flat ordered list for the graph to iterate.
            - "new_template_proposals": list of proposed new templates.
        """
        # ── Layer 1: Global Setup (only on first module) ──
        if include_global_setup:
            print("  🌍 Layer 1: Planning Global Setup...")
            layer1 = self.plan_global_setup(module_brief=module_description)
            logger.info(
                "Layer 1 planned: %d global setup tasks",
                len(layer1.get("global_setup_tasks", [])),
            )
        else:
            print("  🌍 Layer 1: Skipped (already done for this session)")
            layer1 = {"global_setup_tasks": []}

        # ── Layer 2: Module Setup ──
        print("  🗂️  Layer 2: Planning Module Setup...")
        layer2 = self.plan_module_setup(module_brief=module_description)
        logger.info(
            "Layer 2 planned: %d module setup tasks",
            len(layer2.get("module_setup_tasks", [])),
        )

        # ── Layer 3: Per-Step Tasks ──
        module_steps = self._extract_module_steps(module_description)

        try:
            brief = (
                json.loads(module_description)
                if isinstance(module_description, str)
                else module_description
            )
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

        layer3_steps: list[dict[str, Any]] = []
        all_proposals: list[dict[str, Any]] = []
        all_step_titles: list[str] = []

        if module_steps:
            for idx, step in enumerate(module_steps):
                step_label = step.get("step_id", f"step_{idx + 1}")
                print(
                    f"  📐 Layer 3: Planning tasks for step "
                    f"{idx + 1}/{len(module_steps)}: {step_label}..."
                )

                step_result = self.plan_step_tasks(
                    step_brief=step,
                    module_context=module_context,
                    current_implementation_steps=all_step_titles or None,
                )

                tasks = step_result.get("step_tasks", [])
                proposals = step_result.get("new_template_proposals", [])

                for task in tasks:
                    task["parent_step"] = step_label

                layer3_steps.append({
                    "step_id": step_label,
                    "tasks": tasks,
                })
                all_proposals.extend(proposals)
                all_step_titles.extend(t.get("title", "") for t in tasks)

                logger.info(
                    "Step '%s' planned: %d sub-duty tasks",
                    step_label,
                    len(tasks),
                )
        else:
            logger.warning(
                "No training steps found in learning_flow, using fallback for Layer 3"
            )
            print("  📐 Layer 3: No training steps found — using fallback...")
            layer3_steps.append({
                "step_id": "fallback",
                "tasks": self._fallback_step_tasks({})["step_tasks"],
            })

        logger.info(
            "Layer 3 planned: %d steps, %d new template proposals",
            len(layer3_steps),
            len(all_proposals),
        )

        # ── Assemble structured layers ──
        layers = {
            "layer_1_global_setup": layer1.get("global_setup_tasks", []),
            "layer_2_per_module": layer2.get("module_setup_tasks", []),
            "layer_3_per_step": layer3_steps,
        }

        # ── Flatten to ordered implementation_steps for the graph ──
        flat_steps: list[dict[str, Any]] = []
        global_tasks = layer1.get("global_setup_tasks", [])
        module_tasks = layer2.get("module_setup_tasks", [])

        if include_global_setup:
            for t in global_tasks:
                flat_steps.append({**t, "layer": 1})

        for t in module_tasks:
            flat_steps.append({**t, "layer": 2})

        for step_entry in layer3_steps:
            for t in step_entry.get("tasks", []):
                flat_steps.append({**t, "layer": 3})

        # Assign global sequential step_ids
        for i, step in enumerate(flat_steps):
            step["step_id"] = i

        overview = (
            f"Execution plan for module with {len(module_steps)} training step(s), "
            f"{len(global_tasks)} global task(s), "
            f"{len(module_tasks)} module task(s), "
            f"{sum(len(e['tasks']) for e in layer3_steps)} per-step task(s)."
        )

        return {
            "overview": overview,
            "layers": layers,
            "implementation_steps": flat_steps,
            "new_template_proposals": all_proposals,
        }

    # ------------------------------------------------------------------
    # Fallback helpers (deterministic, no LLM needed)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_global_setup() -> dict[str, Any]:
        return {
            "global_setup_tasks": [
                {
                    "task_id": "global_1",
                    "title": "Instantiate the Scenery",
                    "description": "Set up the physical environment using EnvironmentHelper.SetupStandardScenary().",
                    "required_assets": [],
                    "required_templates": [],
                },
                {
                    "task_id": "global_2",
                    "title": "Create Exercise Wrapper",
                    "description": "Instantiate the Exercise root via ExerciseBuilder.",
                    "required_assets": [],
                    "required_templates": [],
                },
                {
                    "task_id": "global_3",
                    "title": "Create Module List Wrapper (MultiProcessStep)",
                    "description": "Add a MultiProcessStep to the Exercise root to hold all modules.",
                    "required_assets": [],
                    "required_templates": [],
                },
            ]
        }

    @staticmethod
    def _fallback_module_setup(module_brief: str) -> dict[str, Any]:
        title = "UnknownModule"
        try:
            brief_dict = json.loads(module_brief)
            title = brief_dict.get("module_title", brief_dict.get("title", title))
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "module_setup_tasks": [
                {
                    "task_id": "module_1",
                    "title": "Create Module Wrapper (ProcessStep)",
                    "description": f"Instantiate a ProcessStep for module '{title}'.",
                    "required_assets": [],
                    "required_templates": [],
                },
                {
                    "task_id": "module_2",
                    "title": "Add Module to Modules List (MultipleProcessStep)",
                    "description": "Register the ProcessStep into the MultipleProcessStep list.",
                    "required_assets": [],
                    "required_templates": [],
                },
            ]
        }

    @staticmethod
    def _fallback_step_tasks(step_brief: dict[str, Any]) -> dict[str, Any]:
        step_id = step_brief.get("step_id", "?")
        return {
            "step_tasks": [
                {
                    "task_id": f"step_{step_id}_instantiate",
                    "title": "Instantiate Visible Objects",
                    "sub_duty": "instantiate_visible_objects",
                    "description": "Spawn required 3D models and UI canvas for this step.",
                    "spawn_3d_models": [],
                    "create_canvas": None,
                    "required_assets": [],
                    "required_templates": [],
                },
                {
                    "task_id": f"step_{step_id}_logic",
                    "title": "Add Exercise Module Logic",
                    "sub_duty": "exercise_module_logic",
                    "description": "Add and configure exercise step components.",
                    "exercise_steps": [],
                    "required_assets": [],
                    "required_templates": [],
                },
                {
                    "task_id": f"step_{step_id}_events",
                    "title": "Bind Logic Events",
                    "sub_duty": "bind_logic_events",
                    "description": "Wire StepEventHandlers, UnityEvents and OnClick listeners.",
                    "step_event_handlers": [],
                    "unity_events": [],
                    "onclick_events": [],
                    "required_assets": [],
                    "required_templates": [],
                },
                {
                    "task_id": f"step_{step_id}_evaluation",
                    "title": "Add Exercise Evaluation",
                    "sub_duty": "exercise_evaluation",
                    "description": "Attach StepEvaluationHandler and GroupEvaluationHandler.",
                    "step_evaluation_handler": {"criteria": ""},
                    "group_evaluation_handler": None,
                    "required_assets": [],
                    "required_templates": [],
                },
            ],
            "new_template_proposals": [],
        }
