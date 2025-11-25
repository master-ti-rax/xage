import os
import subprocess
import sys
from pathlib import Path

def main():
    # Workspace root is where this script is located
    workspace_root = Path(__file__).parent.resolve()
    
    # Path to RoslynValidator project
    validator_project = workspace_root / "src" / "tools" / "RoslynValidator" / "RoslynValidator.csproj"
    
    # Target file path provided by user
    target_file_rel = "../../unity/MASTER_Studio/Assets/Scripts/SceneLogic.cs"
    target_file = (workspace_root / target_file_rel).resolve()
    
    print(f"Looking for file at: {target_file}")
    
    if not target_file.exists():
        print(f"File not found at {target_file}")
        # Try to find it as a sibling to the repositories folder?
        # If workspace is /home/amartis/repositories/eXRage
        # ../../unity is /home/amartis/unity
        
        # Let's try ../unity (sibling in repositories)
        sibling_unity = (workspace_root.parent / "unity" / "MASTER_Studio" / "Assets" / "Scripts" / "SceneLogic.cs").resolve()
        if sibling_unity.exists():
            print(f"Found file at sibling directory: {sibling_unity}")
            target_file = sibling_unity
        else:
            print("Could not find the file. Please check the path.")
            # We will try to run it anyway in case it's a valid path that python's exists() missed for some reason (unlikely)
            # or just let the user know.
            return

    cmd = [
        "dotnet", "run",
        "--project", str(validator_project),
        "--",
        str(target_file)
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    # Force English output for .NET CLI
    env = os.environ.copy()
    env["DOTNET_CLI_UI_LANGUAGE"] = "en-US"
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"Failed to run validator: {e}")

if __name__ == "__main__":
    main()
