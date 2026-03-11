from typing import TypedDict

from prompts.compilation_errors_content import COMPILATION_ERROR_CONTENT
from prompts.semantic_verification_content import SEMANTIC_VERIFICATION_CONTENT 
from prompts.verify_template_usage_content import VERIFY_TEMPLATE_USAGE_CONTENT 

from langchain.tools import tool


class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str  # Unique identifier for the skill
    description: str  # 1-2 sentence description to show in system prompt
    content: str  # Full skill content with detailed instructions

SKILLS: list[Skill] = [
    {
        "name": "analyze_compilation_errors",
        "description": "Reviews C# compilation diagnostics and explains any errors or warnings found.",
        "content": COMPILATION_ERROR_CONTENT,
    },

     {
        "name": "verify_template_usage",
        "description": "Checks if the generated code correctly uses available C# templates instead of reimplementing existing functionality.",
        "content": VERIFY_TEMPLATE_USAGE_CONTENT,
    },

     {
        "name": "semantic_verification",
        "description": "Verifies that each requirement from the implementation step is correctly implemented in the code, following Unity and C# best practices.",
        "content": SEMANTIC_VERIFICATION_CONTENT,
    },
]


def make_load_skill(runtime_data: dict):
    """
        The content of the skills are dinamics, so we need to create the tool at runtime 
        to be able to inject the dinamyc content ( code and templates)
    """
    @tool
    def load_skill(skill_name: str) -> str:
        """Load the full content of a skill into the agent's context.

        Use this when you need detailed information about how to handle a specific
        type of request. This will provide you with comprehensive instructions,
        policies, and guidelines for the skill area.

        Args:
            skill_name: The name of the skill to load (e.g., "expense_reporting", "travel_booking")
        """
        # Find and return the requested skill
        for skill in SKILLS:
            if skill["name"] == skill_name:
                return f"Loaded skill: {skill_name}\n\n{skill['content'].format_map(runtime_data)}"

        # Skill not found
        available = ", ".join(s["name"] for s in SKILLS)
        return f"Skill '{skill_name}' not found. Available skills: {available}"
    return load_skill