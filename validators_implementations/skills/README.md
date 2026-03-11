## Validator Agent - Skill Architecture

The validator agent uses **progressive disclosure** to manage context efficiently.
Instead of loading all validation rules upfront, each check is a separate skill
loaded on-demand via the `load_skill` tool.

### Skills
- **analyze_compilation_errors**: loads compilation diagnostics and rules
- **verify_template_usage**: loads available C# templates and verification rules  
- **semantic_verification**: loads semantic correctness rules

### Why Progressive Disclosure
- System prompt is lighter — only skill descriptions, not full content
- Input prompt is leaner — `compilation_errors` and `available_templates` 
  are injected only inside the relevant skill content
- Easy to extend — add new skills without touching the core validator logic

### Dynamic Tool Injection
Since runtime data (`compilation_errors`, `available_templates`) is only available 
inside `validate_implementation_step()`, the `load_skill` tool is built dynamically 
via closure (`make_load_skill`) and the agent is rebuilt at runtime before each invocation.
See `src/agents/validator_agent.py` and `src/validators_implementations/skills.py`.

### Validation Vector
The final JSON includes a `validation_vector: [compilation, template, semantic]`
where each value is `1` (pass) or `0` (fail), enabling quantitative evaluation
across different code generation architectures.

## 📁 Structure
```
project/
├── artifacts/
├── prompts/
│   ├── compilation_errors_content.py     # compilation skill description
│   ├── semantic_verification_content.py  # semantic skill description
│   ├── validator_prompts.py              # main agent prompts
│   └── verify_template_usage_content.py  # template skill description
├── src/
│   ├── agents/                           # validator agent
│   ├── core/                             # main classes like BaseAgent and LLMConfig
│   ├── tools/                            # RoslynValidator and compilation error fetcher
│   └── utils/                            
├── .env                                  # environment variable
├── README.md                             # documentazione
├── SceneLogic.cs                         # The RoslynValidator write the code here
├── skills.py                             # skills and tool definition 
└── main.py                               # test the validator
```