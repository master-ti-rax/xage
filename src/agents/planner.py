"""Planner Agent for creating execution plans."""

from __future__ import annotations

import json
import re
from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.planner_prompts import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_INPUT_PROMPT,
)
from src.tools.langchain_tools import get_planner_tools
from src.utils.cleaning import clean_agent_output


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
        
        super().__init__(
            name="PlannerAgent",
            model=model,
           # tools=get_planner_tools(),
            system_prompt=PLANNER_SYSTEM_PROMPT,
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
        # Format the input prompt
        input_text = PLANNER_INPUT_PROMPT.format(
            task_description=task_description
        )
        
        # Invoke the agent
        state = {"messages": [{"role": "user", "content": input_text}]}
        result = self.invoke(state)
        
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
