"""Load C# template descriptions from UNITY_SCRIPTS_PATH.

Provides a helper to extract XML doc `/// <summary>` comments and nearby
comment blocks from C# files (excluding Scene.cs) so agents can consume
human-readable template descriptions.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple


def _extract_xml_summaries(lines: List[str]) -> List[Tuple[int, str]]:
    """Return list of (line_index, summary_text) for XML triple-slash summaries."""
    results: List[Tuple[int, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i].lstrip()
        if line.startswith('///'):
            # collect consecutive /// lines
            j = i
            collected = []
            while j < len(lines) and lines[j].lstrip().startswith('///'):
                collected.append(lines[j].lstrip().lstrip('/') )
                j += 1
            # Join and extract inside <summary> if present
            text = "\n".join(collected)

            # Skip if <ignore> tag is present
            if '<ignore>' in text:
                i = j
                continue

            m = re.search(r'<summary>(.*?)</summary>', text, re.DOTALL)
            summary = m.group(1).strip() if m else text.strip()
            results.append((j, re.sub(r'\s+', ' ', summary)))
            i = j
        else:
            i += 1
    return results


def _extract_block_comments(lines: List[str]) -> List[Tuple[int, str]]:
    """Extract /* ... */ block comments and return (line_after_block, text)."""
    results: List[Tuple[int, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '/*' in line:
            start = i
            j = i
            block = []
            while j < len(lines):
                block.append(lines[j])
                if '*/' in lines[j]:
                    j += 1
                    break
                j += 1
            text = '\n'.join(block)

            # Skip if <ignore> tag is present
            if '<ignore>' in text:
                i = j
                continue

            # remove /* */
            text = re.sub(r'/\*+|\*+/','', text)
            results.append((j, re.sub(r'\s+', ' ', text).strip()))
            i = j
        else:
            i += 1
    return results


def get_template_descriptions(scripts_dir: str | None = None, descriptions_only: bool = False) -> str:
    """Scan C# script files under `scripts_dir` (defaults to UNITY_SCRIPTS_PATH or assets/Scripts)
    and return a human-readable aggregated string of template descriptions.

    Excludes `Scene.cs` by design.
    """
    if scripts_dir is None:
        # assume repo root relative path
        env_path = os.getenv("UNITY_SCRIPTS_PATH")
        if env_path:
            scripts_dir = env_path if os.path.isabs(env_path) else os.path.join(os.getcwd(), env_path)
        else:
            scripts_dir = os.path.join(os.getcwd(), 'assets', 'Scripts')

    if not os.path.isdir(scripts_dir):
        return ""

    outputs: List[str] = []
    for fname in sorted(os.listdir(scripts_dir)):
        if not fname.endswith('.cs'):
            continue
        if fname.lower() == 'scene.cs':
            continue
        path = os.path.join(scripts_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue

        # Extract xml summaries and block comments
        summaries = _extract_xml_summaries(lines)
        blocks = _extract_block_comments(lines)

        entries: List[str] = []
        for pos, text in summaries + blocks:
            # find the next non-empty lines to use as signature (handling multi-line)
            sig = "(unknown)"
            k = pos
            while k < len(lines) and lines[k].strip() == '':
                k += 1
            if k < len(lines):
                sig_parts = []
                while k < len(lines):
                    curr = lines[k].strip()
                    if curr:
                        sig_parts.append(curr)
                        combined = " ".join(sig_parts)
                        if '(' in combined:
                            # Stop if we found closing parenthesis or start of body/end of statement
                            if ')' in combined or '{' in curr or ';' in curr:
                                break
                        else:
                            # Likely a class, enum or property - usually one line
                            break
                    k += 1
                sig = re.sub(r'\s+', ' ', " ".join(sig_parts)).strip()
                # Remove opening brace if collected
                if '{' in sig:
                    sig = sig.split('{')[0].strip()

            # attempt to extract a symbol name (function/class/enum) from the signature
            symbol = None
            # class/struct/interface/enum
            m = re.search(r"\b(class|struct|interface|enum)\s+([A-Za-z_]\w*)", sig)
            if m:
                symbol = m.group(2)
            else:
                # method with return type: "public static GameObject CreateExercise(string title, ..."
                m2 = re.search(r"\b[A-Za-z_][\w<>\[\]]*\s+([A-Za-z_]\w*)\s*\(", sig)
                if m2:
                    symbol = m2.group(1)
                else:
                    # fallback: name before parenthesis
                    m3 = re.search(r"([A-Za-z_]\w*)\s*\(", sig)
                    if m3:
                        symbol = m3.group(1)

            if descriptions_only:
                if symbol:
                    entries.append(f"{symbol}: {text}")
                else:
                    entries.append(f"Description: {text}")
            else:
                entries.append(f"Function: {sig}\nDescription: {text}\n")

        if entries:
            if descriptions_only:
                outputs.append(f"\n".join(entries))
            else:
                outputs.append(f"\n{fname}\n".join(entries))

    return "\n\n".join(outputs)


def get_templates_structured(scripts_dir: str | None = None) -> Dict[str, List[Dict[str, str]]]:
    """Scan C# script files and return structured template data.
    
    Returns a dictionary mapping filenames to lists of template items.
    Each template item contains: symbol, signature, description, and filename.
    
    Excludes Scene.cs by design.
    """
    if scripts_dir is None:
        env_path = os.getenv("UNITY_SCRIPTS_PATH")
        if env_path:
            scripts_dir = env_path if os.path.isabs(env_path) else os.path.join(os.getcwd(), env_path)
        else:
            scripts_dir = os.path.join(os.getcwd(), 'assets', 'Scripts')

    if not os.path.isdir(scripts_dir):
        return {}

    templates: Dict[str, List[Dict[str, str]]] = {}
    
    for fname in sorted(os.listdir(scripts_dir)):
        if not fname.endswith('.cs'):
            continue
        if fname.lower() == 'scene.cs':
            continue
            
        path = os.path.join(scripts_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            continue

        # Extract xml summaries and block comments
        summaries = _extract_xml_summaries(lines)
        blocks = _extract_block_comments(lines)

        file_templates: List[Dict[str, str]] = []
        
        for pos, text in summaries + blocks:
            # find the next non-empty, non-comment line to use as signature
            sig = "(unknown)"
            k = pos
            while k < len(lines) and lines[k].strip() == '':
                k += 1
            if k < len(lines):
                sig_parts = []
                while k < len(lines):
                    curr = lines[k].strip()
                    if curr:
                        sig_parts.append(curr)
                        combined = " ".join(sig_parts)
                        if '(' in combined:
                            if ')' in combined or '{' in curr or ';' in curr:
                                break
                        else:
                            break
                    k += 1
                sig = re.sub(r'\s+', ' ', " ".join(sig_parts)).strip()
                if '{' in sig:
                    sig = sig.split('{')[0].strip()

            # attempt to extract a symbol name (function/class/enum) from the signature
            symbol = None
            # class/struct/interface/enum
            m = re.search(r"\b(class|struct|interface|enum)\s+([A-Za-z_]\w*)", sig)
            if m:
                symbol = m.group(2)
            else:
                # method with return type: "public static GameObject CreateExercise(string title, ..."
                m2 = re.search(r"\b[A-Za-z_][\w<>\[\]]*\s+([A-Za-z_]\w*)\s*\(", sig)
                if m2:
                    symbol = m2.group(1)
                else:
                    # fallback: name before parenthesis
                    m3 = re.search(r"([A-Za-z_]\w*)\s*\(", sig)
                    if m3:
                        symbol = m3.group(1)

            file_templates.append({
                "symbol": symbol or "Unknown",
                "signature": sig,
                "description": text,
                "filename": fname
            })

        if file_templates:
            templates[fname] = file_templates

    return templates


def format_templates_for_agent(templates: Dict[str, List[Dict[str, str]]] | None = None, 
                               include_signatures: bool = True) -> str:
    """Format structured templates into a human-readable string for agent consumption.
    
    Args:
        templates: Structured template data. If None, will be loaded automatically.
        include_signatures: Whether to include full function signatures (default: True).
        
    Returns:
        Formatted string describing available templates.
    """
    if templates is None:
        templates = get_templates_structured()
    
    if not templates:
        return "No templates available."
    
    output_parts: List[str] = []
    
    for filename, items in templates.items():
        output_parts.append(f"## {filename}")
        for item in items:
            if include_signatures:
                output_parts.append(f"- {item['symbol']}")
                # Remove "public static " from the beginning of signatures
                clean_sig = item['signature'].replace("public static ", "").strip()
                output_parts.append(f"Signature: `{clean_sig}`")
                output_parts.append(f"Description: {item['description']}")
            else:
                output_parts.append(f"- **{item['symbol']}**: {item['description']}")
        output_parts.append("")  # blank line between files
    
    return "\n".join(output_parts)
