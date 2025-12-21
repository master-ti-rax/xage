"""Simple test to verify the workflow model is ready."""

import json
from dotenv import load_dotenv
from src.graph import run_workflow

# Load environment variables from .env file
load_dotenv()


def test_workflow_basic():
    """Test basic workflow execution with a minimal educational plan."""
    
    # Create a minimal Educational Plan
    educational_plan = {
        "title": "Safety Training Module",
        "modules": [
            {
                "id": "MODULE_1",
                "name": "Safety Basics",
                "steps": [
                    {
                        "id": "STEP_1_1",
                        "description": "The user wears the safety gloves.",
                    }
                ]
            }
        ]
    }
    
    print("="*70)
    print("Testing Workflow Model")
    print("="*70)
    print(f"\nEducational Plan:")
    print(json.dumps(educational_plan, indent=2))
    print("\nRunning workflow...")
    print("-"*70)
    
    try:
        # Run the workflow with debug output
        result = run_workflow(
            goal="Test VR Safety Training Application",
            educational_plan=educational_plan,
            debug=True,
        )
        
        print("-"*70)
        print("\n✅ Workflow completed successfully!")
        print(f"\nFinal State Summary:")
        print(f"  • Completed tasks: {len(result.get('completed_tasks', []))}")
        print(f"  • History events: {len(result.get('history', []))}")
        print(f"  • Errors: {len(result.get('errors', []))}")
        
        if result.get('errors'):
            print(f"\n⚠️  Errors encountered:")
            for err in result['errors']:
                print(f"  - {err}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow failed with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_workflow_basic()
    exit(0 if success else 1)
