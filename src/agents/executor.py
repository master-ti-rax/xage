"""Executor Agent for incremental C# code generation."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.executor_prompts import (
    EXECUTOR_SYSTEM_PROMPT,
    EXECUTOR_INPUT_PROMPT_INITIAL,
    EXECUTOR_INPUT_PROMPT_REFINEMENT,
)
from src.utils.templates import get_templates_structured, format_templates_for_agent, filter_templates_by_requirements

logger = logging.getLogger(__name__)


class ExecutorAgent(BaseAgent):
    """Executor Agent that generates incremental C# Unity code.

    The executor receives an implementation step and writes ONLY the new code
    for that step.  The host system (code_assembler) handles inserting the
    output into the full file with step markers.
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
    ) -> None:
        model = BaseModel(config=llm_config).client

        unity_version = os.getenv("UNITY_VERSION", "2022.3")
        xr_framework = os.getenv("UNITY_XR_FRAMEWORK", "XR Interaction Toolkit")

        formatted_system_prompt = EXECUTOR_SYSTEM_PROMPT.format(
            unity_version=unity_version,
            xr_framework=xr_framework,
        )

        super().__init__(
            name="ExecutorAgent",
            model=model,
            tools=[],
            system_prompt=formatted_system_prompt,
        )

    def implement_step(
        self,
        implementation_step: dict[str, Any] | str,
        existing_code: str,
        retrieved_assets: dict[str, Any] | None = None,
        validation_feedback: str | None = None,
        scene_hierarchy: dict[str, Any] | None = None,
        step_code: str | None = None,
    ) -> str:
        """Generate the C# code for a single implementation step.

        Args:
            implementation_step: The specific step to implement.
            existing_code: The full assembled C# file (read-only context for the LLM).
            retrieved_assets: Retrieved knowledge and 3D models from Asset Manager.
            validation_feedback: Feedback from the Validator if the previous attempt failed.
            scene_hierarchy: The static Object Hierarchy defined by the Planner.
            step_code: The current step's previous code (for refinement only).

        Returns:
            Raw C# code lines for the current step only (not the full file).
        """

        if isinstance(implementation_step, dict):
            step_title = str(implementation_step.get("title", "")).strip() or "N/A"
            step_what = str(implementation_step.get("what", "")).strip() or "N/A"
        else:
            step_title = "N/A"
            if isinstance(implementation_step, str):
                sanitized = implementation_step.strip()
                if len(sanitized) > 300:
                    sanitized = sanitized[:297] + "..."
                step_what = sanitized or "N/A"
            else:
                step_what = "N/A"

        # Format asset context
        assets_context = "None provided."
        if retrieved_assets:
            knowledge_items = retrieved_assets.get("retrieved_knowledge", [])
            model_items = retrieved_assets.get("retrieved_models", [])

            knowledge_lines: list[str] = []
            for item in knowledge_items:
                topic = str(item.get("topic", "N/A")).strip()
                instructions = item.get("instructions") or item.get("summary") or "N/A"
                instructions_str = str(instructions).strip()
                if len(instructions_str) > 300:
                    instructions_str = instructions_str[:297] + "..."
                knowledge_lines.append(f"- {topic}: {instructions_str}")

            asset_lines: list[str] = []
            for item in model_items:
                name = str(item.get("name", "N/A")).strip()
                path = item.get("path") or item.get("asset_path") or item.get("url") or "N/A"
                asset_lines.append(f"- Name: {name}\n  Path: {path}")

            if asset_lines:
                assets_context = "\n".join(asset_lines)

        # Get structured templates and filter to only those required by this step
        templates_structured = get_templates_structured()
        required_templates = implementation_step.get("required_templates") if isinstance(implementation_step, dict) else None
        if required_templates:
            templates_structured = filter_templates_by_requirements(templates_structured, required_templates)
        templates_text = format_templates_for_agent(templates_structured, include_signatures=True)

        scene_hierarchy_str = json.dumps(scene_hierarchy, indent=2) if scene_hierarchy else "None provided."

        # Format the input prompt
        if validation_feedback:
            input_text = EXECUTOR_INPUT_PROMPT_REFINEMENT.format(
                step_title=step_title,
                step_what=step_what,
                assets=assets_context,
                knowledge=templates_text,
                existing_code=existing_code,
                validation_feedback=validation_feedback,
                scene_hierarchy=scene_hierarchy_str,
                step_code=step_code or "// No previous code available",
            )
        else:
            input_text = EXECUTOR_INPUT_PROMPT_INITIAL.format(
                step_title=step_title,
                step_what=step_what,
                assets=assets_context,
                knowledge=templates_text,
                existing_code=existing_code if existing_code else "// Empty file — first step.",
                scene_hierarchy=scene_hierarchy_str,
            )

        state = {
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": input_text},
            ]
        }
        result = self.invoke(state)

        return result["messages"][-1].content
