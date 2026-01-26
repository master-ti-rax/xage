#!/usr/bin/env python3
"""
Main entry point for the Xage workflow.
Usage: python main.py <path_to_educational_plan.json> [--goal "Goal description"] [--debug]
"""

import argparse
import json
import os
import sys
import traceback
from dotenv import load_dotenv

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph import run_workflow

# Load environment variables
load_dotenv()

def load_educational_plan(file_path: str) -> dict:
    """Load and validate the educational plan JSON."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Educational plan file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
        return plan
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in educational plan file: {e}")
    except Exception as e:
        raise Exception(f"Error reading educational plan: {e}")

def print_result_summary(result: dict):
    """Print a summary of the workflow execution result."""
    print("-" * 70)
    print("\n✅ Workflow completed successfully!")
    print(f"\nFinal State Summary:")
    print(f"  • Completed tasks: {len(result.get('completed_tasks', []))}")
    print(f"  • History events: {len(result.get('history', []))}")
    print(f"  • Errors: {len(result.get('errors', []))}")
    
    if result.get('errors'):
        print(f"\n⚠️  Errors encountered:")
        for err in result['errors']:
            print(f"  - {err}")

def main():
    parser = argparse.ArgumentParser(description="Run the Xage AI Agent Workflow.")
    parser.add_argument(
        "plan_path", 
        type=str, 
        help="Path to the educational plan JSON file."
    )
    parser.add_argument(
        "--goal", 
        type=str, 
        default=None, 
        help="Specific goal for the workflow. If not provided, uses the plan title."
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug output."
    )

    args = parser.parse_args()

    try:
        print("="*70)
        print("Xage Workflow Entry Point")
        print("="*70)

        # Load Plan
        print(f"Loading educational plan from: {args.plan_path}")
        educational_plan = load_educational_plan(args.plan_path)
        
        # Determine Goal
        goal = args.goal
        if not goal:
            # Try to get title from root or nested use_case_metadata
            goal = educational_plan.get("title")
            if not goal and "use_case_metadata" in educational_plan:
                goal = educational_plan["use_case_metadata"].get("title")
            
            if not goal:
                goal = "VR Educational Scenario"

            print(f"Goal derived from plan: {goal}")
        else:
            print(f"Goal provided: {goal}")

        print("\nRunning workflow...")
        print("-" * 70)
        
        # Execute Workflow
        result = run_workflow(
            goal=goal,
            educational_plan=educational_plan,
            debug=args.debug
        )
        
        # Output Results
        print_result_summary(result)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ JSON Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Workflow failed with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
	
