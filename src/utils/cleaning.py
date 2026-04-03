"""Utility functions for cleaning and processing agent outputs."""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _extract_balanced_json(text: str) -> str | None:
    """Return the first balanced {...} or [...] block found in text.

    Scans character by character to find the outermost JSON container,
    correctly skipping string literals and handling nesting. Returns the
    substring if found, or None if no balanced block exists.
    """
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        idx = text.find(start_char)
        if idx == -1:
            continue
        depth = 0
        in_string = False
        escape_next = False
        for i in range(idx, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    return text[idx: i + 1]
    return None


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
        # Strategy 1: explicit ```json ... ``` fence
        match = re.search(r"```json\s*(.*?)\s*```", cleaned_output, re.DOTALL)
        if match:
            candidate = match.group(1)
            # Try the fenced content directly, then fall back to balanced extract
            for src in (candidate, _extract_balanced_json(candidate)):
                if src is None:
                    continue
                try:
                    return json.loads(src)
                except json.JSONDecodeError:
                    pass

        # Strategy 2: generic ``` ... ``` fence
        match = re.search(r"```\s*(.*?)\s*```", cleaned_output, re.DOTALL)
        if match:
            candidate = _extract_balanced_json(match.group(1))
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass

        # Strategy 3: balanced-brace extract from raw text
        candidate = _extract_balanced_json(cleaned_output)
        if candidate:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        logger.warning(
            "Failed to parse JSON from agent output (first 500 chars): %s",
            cleaned_output[:500],
        )
        return {}

    if output_type == "csharp":
        code_match = re.search(r'```csharp(.*?)```', cleaned_output, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        code_match = re.search(r'```(.*?)```', cleaned_output, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        return cleaned_output

    return cleaned_output
