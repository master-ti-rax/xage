"""Utility functions for cleaning and processing agent outputs."""

import re
import json
from typing import Any

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
                # Try to find just the JSON object if no code blocks
                match = re.search(r"\{.*\}", cleaned_output, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    json_str = cleaned_output
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Return empty dict or original string if parsing fails? 
            # Better to return empty dict to avoid crashing, but logging is needed by caller
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
