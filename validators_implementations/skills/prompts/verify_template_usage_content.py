VERIFY_TEMPLATE_USAGE_CONTENT = r"""# Verify Template Usage

## Available Templates
{available_templates}

**Your Task**
Check if the code correctly uses the available templates. The implementation should leverage existing template functions/classes rather than reinventing functionality. If a template exists for the required functionality but wasn't used, this is a potential issue.

**CRITICAL: Determining validation_status:**
- **The analysis is Successful ONLY if Appropriate templates are used (if applicable)
- **The analysis is Failure ONLY if Required template functions are NOT used when they should be

"""