#!/usr/bin/env python3
"""
Main entry point for the Xage workflow.
Usage: python main.py <path_to_educational_plan> [--debug]

Supports both PDF and JSON educational plan files.
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
from src.tools.pdf_parser import load_educational_plan
from src.config import configure_logging
from src.tools.neo4j_tools import upload_to_neo4j

# Load environment variables
load_dotenv()

# Configure logging (respects LOG_LEVEL env var)
configure_logging()

def print_result_summary(result: dict):
    """Print a summary of the workflow execution result."""
    print("-" * 70)
    print("\n✅ Workflow completed successfully!")
    print(f"\nFinal State Summary:")
    print(f"  • Completed modules: {len(result.get('completed_modules', []))}")
    print(f"  • History events: {len(result.get('history', []))}")
    print(f"  • Errors: {len(result.get('errors', []))}")
    
    if result.get('errors'):
        print(f"\n⚠️  Errors encountered:")
        for err in result['errors']:
            print(f"  - {err}")

def main():
    parser = argparse.ArgumentParser(description="Run the Xage Workflow.")
    parser.add_argument(
        "plan_path", 
        type=str, 
        help="Path to the educational plan file (PDF or JSON)."
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug output."
    )
    parser.add_argument(
        "--upload-neo4j",
        action="store_true",
        help="Upload the execution graph to Neo4j database after the run completes."
    )

    args = parser.parse_args()

    try:
        print("="*70)
        print("Xage Workflow Entry Point")
        print("="*70)

        # Load Plan
        print(f"Loading educational plan from: {args.plan_path}")
        educational_plan = load_educational_plan(args.plan_path)

        print("\nRunning workflow...")
        print("-" * 70)
        
        # Execute Workflow
        result = run_workflow(
            educational_plan=educational_plan,
            debug=args.debug
        )
        
        if args.upload_neo4j:
            print("-" * 70)
            upload_to_neo4j()

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
	
