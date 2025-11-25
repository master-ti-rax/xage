"""Validator Agent for QA testing."""

from __future__ import annotations

import json
import re
from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.validator_prompts import (
    VALIDATOR_SYSTEM_PROMPT,
    VALIDATOR_INPUT_PROMPT,
)
from src.tools.langchain_tools import get_validator_tools
from src.utils.cleaning import clean_agent_output


class ValidatorAgent(BaseAgent):
    """Validator Agent for QA testing of completed tasks.
    
    The validator determines if a development task was completed successfully
    by formulating a test plan and querying the live Unity scene.
    """

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
    ) -> None:
        """Initialize the Validator Agent.
        
        Args:
            llm_config: LLM configuration. If None, uses default from environment.
        """
        model = BaseModel(config=llm_config).client
        
        super().__init__(
            name="ValidatorAgent",
            model=model,
            tools=get_validator_tools(),
            system_prompt=VALIDATOR_SYSTEM_PROMPT,
        )

    def validate_implementation_step(
        self,
        generated_code: str,
        implementation_step: dict[str, Any],
        retrieved_assets: dict[str, Any] | None = None,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """Validate if a task was completed successfully.
        
        Args:
            generated_code: Full C# script produced by the executor.
            implementation_step: The specific implementation step to validate.
            retrieved_assets: Dictionary of assets retrieved for this task.
            file_path: Optional path to the generated file in the Unity project.
        
        Returns:
            Dict with validation_status, checks_performed, and reasoning.
        """
        
        title = implementation_step.get("title", "")
        what = implementation_step.get("what", "")
        step_description = f"Step: {title}\nRequirement: {what}"

        # Format the input prompt
        input_text = VALIDATOR_INPUT_PROMPT.format(
            step_description=step_description,
            retrieved_assets=json.dumps(retrieved_assets, indent=2) if retrieved_assets else "None",
            generated_code=generated_code,
            file_path=file_path or "Not provided (using temporary file)",
        )
        
        # Invoke the agent
        state = {"messages": [{"role": "user", "content": input_text}]}
        result = self.invoke(state)
        
        content = result["messages"][-1].content
        
        # Parse JSON from content
        validation_result = clean_agent_output(content, output_type="json")
        
        if validation_result:
            return validation_result
        else:
            # Fallback if parsing fails
            return {
                "validation_status": "Failure",
                "checks_performed": [],
                "reasoning": f"Failed to parse Validator output. Raw content: {content[:200]}..."
            }
