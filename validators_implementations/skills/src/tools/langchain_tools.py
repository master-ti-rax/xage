"""LangChain-compatible tool definitions for agents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import subprocess
import tempfile
import json

from langchain.tools import tool


# ============================================================================
# C# Diagnostics Tools
# ============================================================================

@tool
def fetch_csharp_errors(code: str, file_path: str | None = None) -> dict[str, Any]:
    """Retrieve compiler diagnostics for generated C# code.

    Args:
        code: Complete C# source code to validate (used if file_path is None).
        file_path: Optional path to the C# file to validate. If provided, this file is checked instead of creating a temp file.

    Returns:
        Dict with compilation diagnostics.
    """
    if not file_path and not code.strip():
        return {
            "status": "error",
            "message": "No C# code or file path provided for validation.",
        }

    tmp_path = None
    target_path = ""

    if file_path:
        target_path = file_path
        if not os.path.exists(target_path):
             return {
                "status": "error",
                "message": f"Provided file path does not exist: {target_path}",
            }
    else:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        target_path = tmp_path

    try:
        # Path to the RoslynValidator project
        validator_dir = Path(__file__).parent / "RoslynValidator"
        project_path = validator_dir / "RoslynValidator.csproj"
        
        # Try to run with dotnet run
        # Note: This requires dotnet SDK to be installed in the environment
        cmd = ["dotnet", "run", "--project", str(project_path), "--", target_path]
        
        # Force English output for .NET CLI
        env = os.environ.copy()
        env["DOTNET_CLI_UI_LANGUAGE"] = "en-US"

        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False,
            env=env
        )
        
        if result.returncode != 0:
            # If dotnet is missing or fails to run
            return {
                "status": "error",
                "message": "Failed to run C# validator. Ensure dotnet SDK is installed.",
                "details": result.stderr or result.stdout or "Unknown error"
            }
            
        # Parse the JSON output from the validator
        try:
            # The output might contain build logs before the JSON. 
            # We should look for the last line or try to find the JSON object.
            # However, dotnet run -v q (quiet) might help, or we can just parse the output.
            # Let's try to find the JSON part.
            output = result.stdout.strip()
            # Find the start of the JSON object
            json_start = output.find('{')
            if json_start != -1:
                json_str = output[json_start:]
                validation_result = json.loads(json_str)
                return validation_result
            else:
                 return {
                    "status": "error",
                    "message": "No JSON output found from validator",
                    "raw_output": output
                }
        except json.JSONDecodeError:
             return {
                "status": "error",
                "message": "Invalid output from C# validator",
                "raw_output": result.stdout
            }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "dotnet command not found. Please install .NET SDK."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error during validation: {str(e)}"
        }
    finally:
        # Clean up temp file if we created one
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

