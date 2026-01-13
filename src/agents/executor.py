"""Executor Agent for C# code modifications."""

from __future__ import annotations

import os
from typing import Any

from src.utils.saving import save_agent_output
from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.executor_prompts import (
    EXECUTOR_SYSTEM_PROMPT,
    EXECUTOR_INPUT_PROMPT_INITIAL,
    EXECUTOR_INPUT_PROMPT_REFINEMENT,
)
from src.utils.templates import get_templates_structured, format_templates_for_agent


class ExecutorAgent(BaseAgent):
    """Executor Agent that modifies C# Unity code.
    
    The executor receives an Execution Plan and modifies existing C# scripts
    to fulfill all instructions. It acts as an expert AI C# programmer for Unity.
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
    ) -> None:
        """Initialize the Executor Agent.
        
        Args:
            llm_config: LLM configuration. If None, uses default from environment.
        """
        model = BaseModel(config=llm_config).client
        
        # Get environment context
        unity_version = os.getenv("UNITY_VERSION", "2022.3")
        xr_framework = os.getenv("UNITY_XR_FRAMEWORK", "XR Interaction Toolkit")
        
        formatted_system_prompt = EXECUTOR_SYSTEM_PROMPT.format(
            unity_version=unity_version,
            xr_framework=xr_framework
        )
        
        super().__init__(
            name="ExecutorAgent",
            model=model,
            tools=[],  # Executor works via pure code generation
            system_prompt=formatted_system_prompt,
        )

    def implement_step(
        self,
        implementation_step: dict[str, Any] | str,
        existing_code: str,
        retrieved_assets: dict[str, Any] | None = None,
        validation_feedback: str | None = None,
    ) -> str:
        """Execute an Execution Plan by modifying C# code.
        
        Args:
            execution_plan: The Execution Plan (instructions from Planner).
            existing_code: The existing C# code to modify.
            retrieved_assets: Optional retrieved knowledge and 3D models from Asset Manager.
            validation_feedback: Optional feedback from the Validator if the previous attempt failed.
        
        Returns:
            The complete modified C# code.
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

        assets_context = "None provided."
        knowledge_context = "None provided."
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
            if knowledge_lines:
                knowledge_context = "\n".join(knowledge_lines)
        

        # Get structured templates and format them for the executor
        # Include full signatures since executor needs to understand exact API calls
        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(templates_structured, include_signatures=True)

        # Format the input prompt
        if validation_feedback:
            input_text = EXECUTOR_INPUT_PROMPT_REFINEMENT.format(
                step_title=step_title,
                step_what=step_what,
                assets=assets_context,
                knowledge=templates_text,
                existing_code=existing_code,
                validation_feedback=validation_feedback,
            )
        else:
            input_text = EXECUTOR_INPUT_PROMPT_INITIAL.format(
                step_title=step_title,
                step_what=step_what,
                assets=assets_context,
                knowledge=templates_text,
                existing_code=existing_code if existing_code else "// No existing code provided. Create a scene at runtime.",
            )
       
        save_agent_output(
            agent_name=f"{self.name}_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
        )
        # Invoke the agent
        state = {"messages": [{"role": "system", "content": self._system_prompt},
                              {"role": "user", "content": input_text}]}
        result = self.invoke(state)
        save_agent_output(
            agent_name=self.name,
            content=result["messages"][-1].content,
            extension=".txt",
            mode="raw",
        )
        return result["messages"][-1].content
