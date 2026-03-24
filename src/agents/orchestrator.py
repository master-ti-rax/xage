"""Orchestrator Agent for managing task execution flow."""

from __future__ import annotations

import json
import re
from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.orchestrator_prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    ORCHESTRATOR_SUMMARY_INPUT_PROMPT,
)
from src.tools.langchain_tools import get_orchestrator_tools
from src.tools.pdf_parser import segment_educational_plan


class OrchestratorAgent(BaseAgent):
    """Orchestrator Agent that coordinates the task execution flow.
    
    The orchestrator parses the Educational Plan, identifies completed modules,
    and determines the next module to execute.
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
    ) -> None:
        """Initialize the Orchestrator Agent.
        
        Args:
            llm_config: LLM configuration. If None, uses default from environment.
        """
        model = BaseModel(config=llm_config).client
        tools = get_orchestrator_tools()

        super().__init__(
            name="OrchestratorAgent",
            model=model,
            tools=tools,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        )

    def get_next_module(
        self,
        segmented_modules: list[dict[str, Any]],
        completed_modules: list[str],
    ) -> dict[str, Any]:
        """Duty 3 (scaffold): return the next module handoff payload.
        
        Args:
            segmented_modules: Segmented modules from duty 1.
            completed_modules: List of completed module IDs.
        
        Returns:
            Dict with 'module_id' and 'description' keys.
        """
        completed_set = {str(module_id) for module_id in completed_modules}

        for module in segmented_modules:
            module_id = module.get("module_id")
            module_id_str = str(module_id) if module_id is not None else ""
            if module_id_str and module_id_str not in completed_set:
                return {
                    "module_id": module_id_str,
                    "description": module,
                }

        return {
            "module_id": "ALL_MODULES_COMPLETE",
            "description": "All modules in the educational plan are complete.",
        }

    def segment_plan(self, educational_plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Duty 1: segment educational plan into executable modules."""
        return segment_educational_plan(educational_plan)

    def summarize_plan(self, educational_plan: dict[str, Any]) -> dict[str, Any]:
        """Duty 2: summarize educational plan for cross-agent context."""
        segmented_modules = self.segment_plan(educational_plan)
        input_text = ORCHESTRATOR_SUMMARY_INPUT_PROMPT.format(
            educational_plan=json.dumps(educational_plan, indent=2),
            segmented_modules=json.dumps(segmented_modules, indent=2),
        )

        state = {
            "messages": [
                {"role": "user", "content": input_text},
            ]
        }

        try:
            result = self.invoke(state)
            content = result["messages"][-1].content
            parsed = self._parse_summary_json(content)
            if isinstance(parsed, dict) and parsed:
                parsed.setdefault("module_sequence", self._module_sequence(segmented_modules))
                return parsed
        except Exception:
            pass

        return self._fallback_summary(educational_plan, segmented_modules)

    def build_module_handoff(
        self,
        module: dict[str, Any],
        plan_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Duty 3 (scaffold): prepare structured module handoff to planner."""
        module_id = module.get("module_id")
        module_title = module.get("title", "")
        outcomes = module.get("learning_outcomes")
        if not isinstance(outcomes, list):
            outcomes = []

        planner_brief = {
            "module_id": module_id,
            "module_title": module_title,
            "module_description": module.get("pedagogical_rationale", ""),
            "learning_outcomes": outcomes,
            "module_data": module,
            "plan_summary": plan_summary,
        }

        return {
            "module": module,
            "plan_summary": plan_summary,
            "planner_brief": planner_brief,
        }

    @staticmethod
    def _module_sequence(segmented_modules: list[dict[str, Any]]) -> list[dict[str, str]]:
        sequence: list[dict[str, str]] = []
        for module in segmented_modules:
            sequence.append(
                {
                    "module_id": str(module.get("module_id", "")),
                    "title": str(module.get("title", "")),
                    "focus": str(module.get("pedagogical_rationale", ""))[:180],
                }
            )
        return sequence

    def _fallback_summary(
        self,
        educational_plan: dict[str, Any],
        segmented_modules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        plans = educational_plan.get("plans", [])
        first_plan = plans[0] if isinstance(plans, list) and plans else {}
        metadata = first_plan.get("metadata", {}) if isinstance(first_plan, dict) else {}

        objectives = first_plan.get("learning_objectives", []) if isinstance(first_plan, dict) else []
        if not isinstance(objectives, list):
            objectives = []

        return {
            "plan_title": metadata.get("title", "Educational Plan"),
            "training_domain": "XR vocational training",
            "high_level_goal": objectives[0] if objectives else "Execute all training modules in sequence.",
            "module_sequence": self._module_sequence(segmented_modules),
            "global_constraints": [
                "Preserve module order from educational plan.",
                "Implement one module at a time with validation loop.",
            ],
            "asset_themes": [t.get("title", "") for t in segmented_modules if t.get("title")],
            "agent_context": "This summary is deterministic fallback output because LLM summarization was unavailable.",
        }

    @staticmethod
    def _parse_summary_json(content: Any) -> dict[str, Any]:
        if not isinstance(content, str):
            return {}

        text = content.strip()
        fenced = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1).strip()
        else:
            object_match = re.search(r"\{.*\}", text, re.DOTALL)
            if object_match:
                text = object_match.group(0)

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
