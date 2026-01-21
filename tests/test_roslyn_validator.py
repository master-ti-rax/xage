#!/usr/bin/env python3
"""
Test script to run Roslyn Validator on Unity SceneLogic.cs
"""
import subprocess
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def test_roslyn_validator():
    # Paths
    repo_root = Path(__file__).parent.parent

    unity_project = repo_root / Path(os.getenv("UNITY_PROJECT_PATH"))
    scene_logic_path = unity_project / Path(os.getenv("UNITY_SCRIPTS_PATH")) / "SceneLogic.cs"
    validator_path = repo_root / "src/tools/RoslynValidator"
    
    # Resolve to absolute paths
    scene_logic_path = scene_logic_path.resolve()
    validator_path = validator_path.resolve()
    
    print(f"Testing Roslyn Validator on: {scene_logic_path}")
    print(f"Validator location: {validator_path}")
    print("-" * 80)
    
    if not scene_logic_path.exists():
        print(f"ERROR: SceneLogic.cs not found at {scene_logic_path}")
        return
    
    # Run the validator
    try:
        result = subprocess.run(
            ["dotnet", "run", "--", str(scene_logic_path)],
            cwd=str(validator_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print("\n" + "=" * 80)
        
        # Parse JSON output
        try:
            # Find JSON in output (skip build warnings)
            lines = result.stdout.strip().split('\n')
            json_line = None
            for line in reversed(lines):
                if line.strip().startswith('{'):
                    json_line = line.strip()
                    break
            
            if json_line:
                validation_result = json.loads(json_line)
                print(f"\nValidation Status: {validation_result['status']}")
                
                if validation_result.get('errors'):
                    print(f"\nErrors found ({len(validation_result['errors'])}):")
                    for error in validation_result['errors']:
                        print(f"  - {error['id']} (line {error['line']}): {error['message']}")
                else:
                    print("\n✅ No errors found!")
            else:
                print("Could not parse JSON output")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            
    except subprocess.TimeoutExpired:
        print("ERROR: Validator timed out")
    except Exception as e:
        print(f"ERROR running validator: {e}")

if __name__ == "__main__":
    test_roslyn_validator()
