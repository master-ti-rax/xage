"""Assembler for incremental C# code generation with step markers.

Instead of regenerating the entire file each step, the executor outputs only
the new code block for the current step.  This module handles:
  - Wrapping step code in marker comments (``// #region Step N`` / ``// #endregion Step N``)
  - Inserting a new step block at the correct location in the file
  - Replacing an existing step block during validation-refinement loops
  - Extracting a step's code block for targeted refinement
"""

from __future__ import annotations

import re
import textwrap

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INSERTION_SENTINEL = "// STEP_INSERTION_POINT"
_BODY_INDENT = "        "  # 8 spaces — inside CreateScene()

# Regex that matches an opening marker: ``// #region Step 3: Some Title``
_REGION_START_RE = re.compile(
    r"^(?P<indent>\s*)//\s*#region\s+Step\s+(?P<num>\d+)(?::\s*(?P<title>.*))?$",
    re.MULTILINE,
)

# Regex that matches a closing marker: ``// #endregion Step 3``
_REGION_END_RE = re.compile(
    r"^(?P<indent>\s*)//\s*#endregion\s+Step\s+(?P<num>\d+)\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def make_step_marker_start(step_number: int, step_title: str) -> str:
    """Return the opening marker comment line (no leading indent)."""
    return f"// #region Step {step_number}: {step_title}"


def make_step_marker_end(step_number: int) -> str:
    """Return the closing marker comment line (no leading indent)."""
    return f"// #endregion Step {step_number}"


def extract_step_code(full_code: str, step_number: int) -> str | None:
    """Extract the code between the markers for *step_number*.

    Returns the raw code lines (preserving original indentation) **without**
    the marker lines themselves, or ``None`` if the markers are not found.
    """
    start_match = None
    for m in _REGION_START_RE.finditer(full_code):
        if int(m.group("num")) == step_number:
            start_match = m
            break
    if start_match is None:
        return None

    end_match = None
    for m in _REGION_END_RE.finditer(full_code, start_match.end()):
        if int(m.group("num")) == step_number:
            end_match = m
            break
    if end_match is None:
        return None

    # Everything between the end of the start-marker line and the beginning
    # of the end-marker line.
    inner = full_code[start_match.end(): end_match.start()]
    # Strip leading/trailing blank lines but keep internal structure.
    return inner.strip("\n")


def replace_step_code(
    full_code: str,
    step_number: int,
    new_code: str,
) -> str:
    """Replace the code block inside *step_number*'s markers with *new_code*.

    The markers themselves are preserved.  Raises ``ValueError`` if the
    markers for the requested step are not found.
    """
    start_match = None
    for m in _REGION_START_RE.finditer(full_code):
        if int(m.group("num")) == step_number:
            start_match = m
            break
    if start_match is None:
        raise ValueError(f"Opening marker for Step {step_number} not found")

    end_match = None
    for m in _REGION_END_RE.finditer(full_code, start_match.end()):
        if int(m.group("num")) == step_number:
            end_match = m
            break
    if end_match is None:
        raise ValueError(f"Closing marker for Step {step_number} not found")

    indented_code = _indent_code(new_code, start_match.group("indent") or _BODY_INDENT)
    replacement = f"\n{indented_code}\n"

    return full_code[: start_match.end()] + replacement + full_code[end_match.start():]


def insert_step_code(
    full_code: str,
    step_number: int,
    step_title: str,
    new_code: str,
) -> str:
    """Insert a new step block (with markers) into *full_code*.

    Insertion strategy (in priority order):
    1. After the last existing ``#endregion Step N`` marker.
    2. At the ``// STEP_INSERTION_POINT`` sentinel (replaced on first use).
    3. Before the final ``}`` of the file (last-resort fallback).
    """
    indent = _BODY_INDENT
    indented_code = _indent_code(new_code, indent)

    block = (
        f"\n{indent}{make_step_marker_start(step_number, step_title)}\n"
        f"{indented_code}\n"
        f"{indent}{make_step_marker_end(step_number)}\n"
    )

    # Strategy 1: after the last #endregion marker
    last_end = None
    for m in _REGION_END_RE.finditer(full_code):
        last_end = m
    if last_end is not None:
        pos = last_end.end()
        return full_code[:pos] + block + full_code[pos:]

    # Strategy 2: replace the sentinel comment
    sentinel_idx = full_code.find(_INSERTION_SENTINEL)
    if sentinel_idx != -1:
        line_start = full_code.rfind("\n", 0, sentinel_idx)
        line_end = full_code.find("\n", sentinel_idx)
        if line_end == -1:
            line_end = len(full_code)
        return full_code[:line_start] + block + full_code[line_end:]

    # Strategy 3: before the last closing brace
    last_brace = full_code.rfind("}")
    if last_brace != -1:
        # Go before the second-to-last brace (class body end)
        second_last = full_code.rfind("}", 0, last_brace)
        if second_last != -1:
            last_brace = second_last
        return full_code[:last_brace] + block + "\n" + full_code[last_brace:]

    # Absolute fallback: append
    return full_code + block


def clean_step_output(raw_output: str) -> str:
    """Strip accidental boilerplate that the LLM may include despite instructions.

    Removes:
    - ``using`` directives
    - Class/method declarations (``public class …``, ``static void CreateScene…``)
    - Step marker comments (added by the assembler, not the LLM)
    - Leading/trailing blank lines
    """
    lines = raw_output.split("\n")
    cleaned: list[str] = []

    skip_patterns = [
        re.compile(r"^\s*using\s+\w"),
        re.compile(r"^\s*(public|private|internal|protected)?\s*(static\s+)?(partial\s+)?class\s+"),
        re.compile(r"^\s*(public|private|internal|protected)?\s*(static\s+)?void\s+CreateScene\s*\("),
        re.compile(r"^\s*//\s*#(end)?region\s+Step\s+\d+"),
    ]

    for line in lines:
        if any(p.match(line) for p in skip_patterns):
            continue
        cleaned.append(line)

    # Repeatedly strip wrapping braces left over from class/method bodies
    result = "\n".join(cleaned).strip()
    while True:
        result_lines = result.split("\n")
        if (
            len(result_lines) >= 3
            and result_lines[0].strip() == "{"
            and result_lines[-1].strip() == "}"
        ):
            result = "\n".join(result_lines[1:-1]).strip()
        else:
            break

    return result.strip()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _indent_code(code: str, indent: str) -> str:
    """Normalize *code* so every non-empty line has exactly *indent* as prefix."""
    dedented = textwrap.dedent(code)
    lines = dedented.split("\n")
    indented_lines: list[str] = []
    for line in lines:
        if line.strip():
            indented_lines.append(indent + line.strip())
        else:
            indented_lines.append("")
    return "\n".join(indented_lines)
