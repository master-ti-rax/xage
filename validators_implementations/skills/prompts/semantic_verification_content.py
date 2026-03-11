SEMANTIC_VERIFICATION_CONTENT = r"""# Semantic Verification

**Your Task**
For each requirement from the step, inspect the code and gather evidence that it is satisfied (e.g., method implementations, serialized fields, event hooks). Reference the relevant class, method, or property names—and quote short code fragments when helpful. Check that the implementation follows Unity and C# best practices.

**IMPORTANT:** Evaluate semantic correctness independently from compilation errors. 
If the logic and structure are correct but there is a compilation error (e.g. missing semicolon), 
the semantic check should still PASS. Compilation errors are evaluated separately.

**CRITICAL: Determining validation_status:**
- **The analysis is Successful ONLY if The current step's requirements are implemented correctly AND Implementation follows Unity/C# best practices
- **The analysis is Failure ONLY if Current step's requirements are NOT implemented or implemented incorrectly OR Critical logic errors or bad practices that would break functionality

"""