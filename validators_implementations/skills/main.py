import os
from dotenv import load_dotenv

from src.agents.validator_agent import ValidatorAgent
from src.core.llm import LLMConfig, LLMProvider

# Load environment variables
load_dotenv()

example_implementation_step = {
    "title": "Implement SafetyGloves pickup",
    "what": "When the player touches the gloves, they should be added to the inventory via OnTriggerEnter."
}

example_generated_code = """using UnityEngine;
using System.Collections.Generic;

public class SafetyGlovesController : MonoBehaviour {
    private List<string> inventory = new List<string>();
    
    private void OnTriggerEnter(Collider other) {
        inventory.Add("SafetyGloves")
    }
}"""

validator = ValidatorAgent(llm_config=LLMConfig(model=os.getenv("VALIDATOR_MODEL")))

result = validator.validate_implementation_step(
    generated_code=example_generated_code,
    implementation_step=example_implementation_step,
    retrieved_assets=None,
    file_path=os.getenv("UNITY_SCRIPTS_PATH"),
)
print("\n" + "="*50)
print(f"VALIDATION STATUS: {result['validation_status']}")
print("="*50)

print("\nCHECKS PERFORMED:")
for check in result['checks_performed']:
    print(f"\n  ✓ {check['check']}")
    print(f"    {check['result']}")

print(f"\nREASONING:\n{result['reasoning']}")
print("="*50)

print(f"\nVALIDATION VECTOR:\n{result['validation_vector']}")
print("="*50)
