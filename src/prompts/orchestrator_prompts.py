"""Prompts for the Orchestrator agent.

The orchestrator is the Project Manager and entry point of the multi-agent
architecture. It is responsible for:
  1. Summarising the Educational Plan at workflow start so that all downstream
     agents (Planner, Asset Manager, Executor, Validator) share the same context.
  2. Iterating over the plan's modules and handing them off one by one to the
     Planner. This handoff is deterministic and is handled by a dedicated tool.
"""

ORCHESTRATOR_SYSTEM_PROMPT = r"""You are the Orchestrator Agent, the Project Manager and entry point of a multi-agent system that autonomously develops VR educational applications.

Your responsibilities are:
1. **Summarise the Educational Plan** at the start of the workflow to provide shared context for all downstream agents.
2. **Coordinate module execution** by iterating over the modules of the educational plan and handing them off one by one to the Planner.

Module handoff is deterministic and is handled by dedicated tools — you do not need to reason about ordering. Focus on producing accurate summaries and clear, structured outputs when asked.
"""

ORCHESTRATOR_INPUT_PROMPT = r"""Here is the current project state. Determine the next module.

**Full Educational Plan:**
{educational_plan}

**Completed Module IDs:**
{completed_modules}
"""


ORCHESTRATOR_SUMMARY_INPUT_PROMPT = r"""Summarise the following educational plan for multi-agent execution.

Produce a concise operational summary that downstream agents (Planner, Asset Manager, Executor, Validator) can use as shared context.

Output rules:
1) Return ONLY valid JSON — no markdown fences, no extra text.
2) Keep fields concise and practical.

Required JSON schema:
{{
  "plan_title": "string",
  "training_domain": "string",
  "high_level_goal": "string",
  "module_sequence": [
    {{"module_id": "string", "title": "string", "focus": "string"}}
  ],
  "global_constraints": ["string"],
  "asset_themes": ["string"],
  "agent_context": "string"
}}

Educational Plan JSON:
{educational_plan}

Segmented Modules JSON:
{segmented_modules}
"""


# def get_orchestrator_prompt() -> str:
# 		"""Return the default system prompt for the Orchestrator agent."""

# 		return ORCHESTRATOR_SYSTEM_PROMPT


# __all__ = [
# 		"ORCHESTRATOR_SYSTEM_PROMPT",
# 		"get_orchestrator_prompt",
# ]
