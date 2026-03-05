"""Utility functions for cleaning and processing agent outputs."""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

def clean_agent_output(output: Any, output_type: str = "text") -> Any:
    """Process and clean agent output, handling thinking blocks and parsing.
    
    Args:
        output: Raw output from the agent (usually a string).
        output_type: Expected output type ("text", "json", "csharp").
        
    Returns:
        Cleaned and parsed output.
    """
    if not isinstance(output, str):
        return output
        
    # Remove <think> blocks
    cleaned_output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
    
    if output_type == "text":
        return cleaned_output
        
    if output_type == "json":
        try:
            # Try to find JSON block
            match = re.search(r"```json\s*(.*?)\s*```", cleaned_output, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # Try to find just the JSON object or array if no code blocks
                match = re.search(r"(\{.*\}|\[.*\])", cleaned_output, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    json_str = cleaned_output
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.exception(
                "Failed to parse JSON from agent output (first 500 chars): %s",
                cleaned_output[:500],
            )
            return {}
            
    if output_type == "csharp":
        # Extract code from markdown blocks
        code_match = re.search(r'```csharp(.*?)```', cleaned_output, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try generic code block
        code_match = re.search(r'```(.*?)```', cleaned_output, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        return cleaned_output
        
    return cleaned_output
