"""Validator Agent for QA testing."""

from __future__ import annotations

import json
from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from prompts.validator_prompts import (
    VALIDATOR_SYSTEM_PROMPT,
    VALIDATOR_INPUT_PROMPT,
)
from src.tools.langchain_tools import fetch_csharp_errors
from src.utils.cleaning import clean_agent_output
from src.utils.saving import save_agent_output
from src.utils.templates import get_templates_structured, format_templates_for_agent
from skills import make_load_skill

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
            tools=[],  # Tools are built dynamically at runtime.
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

        # Pre-fetch compilation errors
        compilation_result = fetch_csharp_errors.invoke({
            "code": generated_code,
            "file_path": file_path
        })

        # Get structured templates for semantic verification
        templates_structured = get_templates_structured()
        templates_text = format_templates_for_agent(templates_structured, include_signatures=True)

        #! LOAD TOOL
        load_skill_tool = make_load_skill({
            "compilation_errors": compilation_result,
            "available_templates": templates_text if templates_text else "No templates available",
        })

        #! REBUILD AGENT WITH TOOLS
        self._rebuild_agent(tools=[load_skill_tool])

        # Format the input prompt
        input_text = VALIDATOR_INPUT_PROMPT.format(
            step_description=step_description,
            retrieved_assets=json.dumps(retrieved_assets, indent=2) if retrieved_assets else "None",
            generated_code=generated_code,
        )
        save_agent_output(
            agent_name=f"{self.name}_prompt",
            content=input_text,
            extension=".txt",
            mode="raw",
        )
        # Invoke the agent
        state = {"messages": [{"role": "user", "content": input_text}]}
        result = self.invoke(state)

        #check for tool calls
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tc in message.tool_calls:
                    print(f"TOOL CALL: {tc['name']}({tc['args']})")

        save_agent_output(
            agent_name=self.name,
            content=result,
            extension=".txt",
            mode="raw",
        )

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
