"""Planner Agent for creating execution plans."""

from __future__ import annotations

import os
import json
import re
from typing import Any

from src.utils.saving import save_agent_output
from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.planner_prompts import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_INPUT_PROMPT,
)
from src.tools.langchain_tools import get_planner_tools
from src.utils.cleaning import clean_agent_output
from src.utils.templates import get_templates_structured, format_templates_for_agent


class PlannerAgent(BaseAgent):
    """Planner Agent that creates execution plans for the Executor.
    
    The planner receives a high-level task and synthesizes it into a clear,
    unambiguous Execution Plan that instructs the Executor (an AI C# programmer)
    on how to modify the Unity scripts.
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
        model = BaseModel(config=llm_config).client
        
        # Get environment context
        unity_version = os.getenv("UNITY_VERSION", "2022.3")
        xr_framework = os.getenv("UNITY_XR_FRAMEWORK", "XR Interaction Toolkit (XRIT)")
        
        formatted_system_prompt = PLANNER_SYSTEM_PROMPT.format(
            unity_version=unity_version,
            xr_framework=xr_framework
        )
        
        super().__init__(
            name="PlannerAgent",
            model=model,
           # tools=get_planner_tools(),
            system_prompt=formatted_system_prompt,
        )

    def create_execution_plan(
        self,
        task_description: str,
    ) -> dict[str, Any]:
        """Create an Execution Plan for the given task.
        
        Args:
            task_description: The high-level task description.
        
        Returns:
            The Execution Plan as a structured dictionary with keys:
            - overview: str
            - implementation_tasks: list[dict]
            - required_knowledge: list[dict]
            - required_assets: list[dict]
            - technical_notes: str
        """
        # Check for existing plan file
        plan_file = "gemini-plan.json"
        if os.path.exists(plan_file):
            print(f"Loading existing plan from {plan_file}")
            
            try:
                with open(plan_file, 'r') as f:
                    execution_plan = json.load(f)
                #return execution_plan
            except Exception as e:
                print(f"Error loading plan from {plan_file}: {e}")
                # Fallback to generation if loading fails
            
        # Load available template descriptions and format the input prompt
        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(templates_structured, include_signatures=False)
        
        # Format the core planner input and append templates for context
        print(task_description)
        input_text = PLANNER_INPUT_PROMPT.format(
            task_description=task_description
        )
        if templates_text:
            input_text = (
                input_text
                + "\n\n**AVAILABLE TEMPLATES:**\n"
                + templates_text
            )

        # Temporary debug: print the full prompt so developers can inspect it.
        # This is intentionally simple and should be removed after debugging.
        # try:
        #     print("[DEBUG Planner Prompt]\n" + input_text, flush=True)
        # except Exception:
        #     pass
        #exit(0)
        save_agent_output(
            agent_name=f"{self.name}_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
        )
        # Invoke the agent
        state = {"messages": [#{"role": "system", "content": self._system_prompt},
                              {"role": "user", "content": input_text}]}
        result = self.invoke(state)

        save_agent_output(
            agent_name=self.name,
            content=result,
            extension=".txt",
            mode="raw",
        )
        # Extract the response content
        response_content = result["messages"][-1].content
        
        # Parse JSON response
        execution_plan = clean_agent_output(response_content, output_type="json")
        
        if execution_plan:
            return execution_plan
        else:
            # Fallback: return raw content wrapped in a basic structure
            print(f"Warning: Failed to parse JSON from planner response")
            return {
                "overview": "Failed to parse structured plan",
                "implementation_tasks": [],
                "required_knowledge": [],
                "required_assets": [],
                "technical_notes": response_content,
                "_raw_response": response_content
            }
