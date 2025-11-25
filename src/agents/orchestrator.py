"""Orchestrator Agent for managing task execution flow."""

from __future__ import annotations

from typing import Any

from src.core.agent import BaseAgent
from src.core.llm import BaseModel, LLMConfig
from src.prompts.orchestrator_prompts import ORCHESTRATOR_SYSTEM_PROMPT, ORCHESTRATOR_INPUT_PROMPT
from src.tools.langchain_tools import get_orchestrator_tools
from src.utils.cleaning import clean_agent_output


class OrchestratorAgent(BaseAgent):
    """Orchestrator Agent that coordinates the task execution flow.
    
    The orchestrator parses the Educational Plan, identifies completed tasks,
    and determines the next task to execute.
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
        
        # Format system prompt with tools list
        tools_description = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in tools
        ])
        #print(ORCHESTRATOR_SYSTEM_PROMPT)
        formatted_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(tools=tools_description)
        
        super().__init__(
            name="OrchestratorAgent",
            model=model,
            tools=tools,
            system_prompt=formatted_prompt,
        )

    def get_next_task(
        self,
        educational_plan: dict[str, Any],
        completed_tasks: list[str],
    ) -> dict[str, Any]:
        """Determine the next task to execute.
        
        Args:
            educational_plan: The full Educational Plan (EP) as a dict.
            completed_tasks: List of completed task IDs.
        
        Returns:
            Dict with 'task_id' and 'description' keys.
        """
        import json
        
        # Format the input prompt
        input_text = ORCHESTRATOR_INPUT_PROMPT.format(
            educational_plan=json.dumps(educational_plan, indent=2),
            completed_tasks=json.dumps(completed_tasks, indent=2),
        )
        print("completed_tasks:", completed_tasks)

        #print("Orchestrator Input Prompt:")
        #print("get the next activity")
        # Invoke the agent
        state = {"messages": [{"role": "user", "content": input_text}]} 
        result = self.invoke(state)
        
        content = result["messages"][-1].content
        print(content)
        
        # Clean and parse the output
        return clean_agent_output(content, output_type="json")
