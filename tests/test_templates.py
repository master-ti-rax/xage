import os
import json
from dotenv import load_dotenv
import sys
from pathlib import Path

# Ensure the project root is in sys.path
root_path = Path(__file__).parent.parent.resolve()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))


from src.utils.templates import (
    get_template_descriptions,
    get_templates_structured,
    format_templates_for_agent
)

# Load environment variables from .env
load_dotenv()

def main():
    scripts_path = os.getenv("UNITY_SCRIPTS_PATH")
    print(f"--- Environment Context ---")
    print(f"UNITY_SCRIPTS_PATH: {scripts_path}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"---------------------------\n")

    print("--- 1. Testing get_templates_structured() ---")
    templates = get_templates_structured()
    if not templates:
        print("No templates found.")
    else:
        print(f"Found templates in {len(templates)} files.")
        # print(json.dumps(templates, indent=2))
    print("\n" + "="*50 + "\n")

    print("--- 2. Testing get_template_descriptions() ---")
    descriptions = get_template_descriptions()
    if not descriptions:
        print("No descriptions generated.")
    else:
        print(descriptions)
    print("\n" + "="*50 + "\n")

    print("--- 3. Testing format_templates_for_agent() ---")
    formatted = format_templates_for_agent(templates, include_signatures=False)
    if not formatted or formatted == "No templates available.":
         print("Formatted output is empty or default.")
    else:
        print(formatted)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
