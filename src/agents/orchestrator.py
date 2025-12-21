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
        
        last_message = result["messages"][-1]
        
        # Check for tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_call = last_message.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"Orchestrator executing tool: {tool_name}")
            
            # Find the tool
            for tool in self._tools:
                if tool.name == tool_name:
                    # Execute the tool
                    return tool.invoke(tool_args)
            
            print(f"Warning: Tool {tool_name} not found in agent tools.")
        
        content = last_message.content
        print(content)
        
        # Check for text-based tool calls (e.g. <tool_call> JSON </tool_call>)
        import re
        tool_call_match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', content, re.DOTALL)
        if tool_call_match:
            json_str = tool_call_match.group(1).strip()
            tool_name = None
            tool_args = {}
            
            try:
                tool_call_json = json.loads(json_str)
                tool_name = tool_call_json.get("name")
                tool_args = tool_call_json.get("arguments")
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse tool call JSON from text: {e}")
                # Fallback: Check if it's the expected tool using regex
                if '"name": "get_next_uncompleted_activity"' in json_str or "'name': 'get_next_uncompleted_activity'" in json_str:
                    print("Fallback: Detected 'get_next_uncompleted_activity' despite JSON error. Using context arguments.")
                    tool_name = "get_next_uncompleted_activity"
                    # We will use the arguments from the method context
                    tool_args = {
                        "educational_plan": educational_plan,
                        "completed_activity_ids": completed_tasks
                    }
            
            if tool_name:
                print(f"Orchestrator executing text-based tool: {tool_name}")
                
                # Special handling for get_next_uncompleted_activity to ensure correct args
                if tool_name == "get_next_uncompleted_activity":
                     # Always use the authoritative data from context to avoid hallucinated/malformed args
                     tool_args = {
                        "educational_plan": educational_plan,
                        "completed_activity_ids": completed_tasks
                    }

                # Find the tool
                for tool in self._tools:
                    if tool.name == tool_name:
                        # Execute the tool
                        return tool.invoke(tool_args)
                
                print(f"Warning: Tool {tool_name} not found in agent tools.")
        
        # Clean and parse the output
        return clean_agent_output(content, output_type="json")
