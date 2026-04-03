# Local change journal (not committed to git)

This file records edits made during active development: **what** changed, **why**, and **before/after** snippets.  
Add a new block for each logical change. Keep raw excerpts short but enough to reproduce the intent.

---

## Template (copy for each new entry)

Use this shape (duplicate the before/after pairs if several files changed):

- **Heading:** `### YYYY-MM-DD — short title`
- **Files:** bullet list of touched paths
- **Problem:** what was wrong or missing
- **Why:** rationale / approach
- **Per file:** `` `path` — before `` then fenced code block with old raw; same for **after**

---

## Entries

*(Oldest / first-in-chat fixes at the top.)*

### 2026-03-20 — Validator output: markdown instead of JSON (`JSONDecodeError`)

**Files:** `src/utils/cleaning.py`, `src/prompts/validator_prompts.py`, `src/agents/validator.py`

**Problem:** The Validator LLM sometimes answered with a markdown report (e.g. `**Validation Report for SceneLogic.cs**`) instead of the required single JSON object. `clean_agent_output(..., output_type="json")` then passed the entire string to `json.loads`, raised `JSONDecodeError`, and `logger.exception` flooded logs with a traceback. Parsing returned `{}`, so the fallback hid almost all of the model text from the Executor (only ~200 chars).

**Why:** Harden JSON extraction (fenced blocks, balanced `{...}` scanning, pick the best-scoring object when prose contains multiple `{`), steer the model with stricter prompt rules, log parse failures as warnings, and on failure keep a large raw excerpt in `reasoning` for the feedback loop.

---

**`src/utils/cleaning.py` — before (excerpt, `output_type == "json"`)**

```python
        try:
            match = re.search(r"```json\s*(.*?)\s*```", cleaned_output, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                match = re.search(r"(\{.*\}|\[.*\])", cleaned_output, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    json_str = cleaned_output
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.exception(
                "Failed to parse JSON from agent output (first 500 chars): %s",
                cleaned_output[:500],
            )
            return {}
```

**`src/utils/cleaning.py` — after (summary)**

- Added `_extract_balanced_json_object`, `_parse_best_json_object`.
- JSON branch: try ``` / ```json fences (with inner brace extract), then best object across all `{` positions, then array regex, then full strip; on failure `logger.warning` and `{}`.

---

**`src/prompts/validator_prompts.py` — before (intent)**

- Asked for a JSON block but allowed a normal prose “final answer” style; no explicit ban on a separate “Validation Report”.

**`src/prompts/validator_prompts.py` — after (excerpt)**

```text
When you have enough information, respond with **nothing else**—no title, no markdown report...
**Do not** output a separate "Validation Report" or narrative outside the JSON.
```

(Input prompt adds: reply with only a ```json ... ``` block.)

---

**`src/agents/validator.py` — before**

```python
        else:
            return {
                "validation_status": "Failure",
                "checks_performed": [],
                "reasoning": f"Failed to parse Validator output. Raw content: {content[:200]}..."
            }
```

**`src/agents/validator.py` — after**

```python
        raw = (content or "")[:12000]
        return {
            "validation_status": "Failure",
            "checks_performed": [],
            "reasoning": (
                "Validator response was not valid JSON. Raw output (truncated):\n" + raw
            ),
        }
```

---

### 2026-03-20 — Scene logic output filename via `.env`

**Files:** `src/graph.py`, `.env`, `README.md`, `.gitignore` (this journal)

**Problem:** The C# file name written by the Executor (`SceneLogicMarco.cs`) was hard-coded in `graph.py`, so switching Unity scripts or class names required editing source.

**Why:** Centralize the output script name in `SCENE_LOGIC_FILENAME` so environments and branches can differ without code changes; default remains `SceneLogic.cs` if unset.

---

**`src/graph.py` — before**

```python
            target_file = scripts_dir / "SceneLogicMarco.cs"
```

(two branches: `UNITY_SCRIPTS_PATH` and `UNITY_PROJECT_PATH` / `Assets/Scripts`)

**`src/graph.py` — after**

```python
def _scene_logic_target_file(scripts_dir: Path) -> Path:
    """Output C# file under scripts_dir; name from SCENE_LOGIC_FILENAME (.env)."""
    fname = (os.getenv("SCENE_LOGIC_FILENAME", "SceneLogic.cs") or "SceneLogic.cs").strip()
    if not fname.endswith(".cs"):
        fname = f"{fname}.cs"
    return scripts_dir / fname

            target_file = _scene_logic_target_file(scripts_dir)
```

**`.env` — after (excerpt)**

```env
SCENE_LOGIC_FILENAME=SceneLogicMarco.cs
```

---

### 2026-03-20 — This local changelog + git ignore

**Files:** `LOCAL_CHANGELOG.md`, `.gitignore`

**Problem:** No single, non-committed place to track ongoing project edits with context.

**Why:** Keep a running diary for the team/machine owner without polluting version history.

---

**`.gitignore` — before**

```
(LOCAL_CHANGELOG.md not listed)
```

**`.gitignore` — after**

```
# Local dev change journal (not for version control)
LOCAL_CHANGELOG.md
```

---

### 2026-03-20 — Asset Manager embeddings CSV filename via `.env`

**Files:** `src/agents/asset_manager.py`, `.env`, `README.md`

**Problem:** The semantic-search / embedding index file was hard-coded as `embeddingsMarco.csv` in `_semantic_search_local` and `_add_embedding_for_folder`, so different environments or indices required editing code.

**Why:** Read `ASSET_EMBEDDINGS_FILENAME` from the environment (default `embeddings.csv`); append `.csv` if omitted. Keeps the same behavior when `.env` sets `embeddingsMarco.csv`.

---

**`src/agents/asset_manager.py` — before**

```python
        embeddings_file = search_path / "embeddingsMarco.csv"
```

(two call sites)

**`src/agents/asset_manager.py` — after**

```python
def _embeddings_csv_filename() -> str:
    """Local embeddings index CSV name (see ASSET_EMBEDDINGS_FILENAME in .env)."""
    fname = (os.getenv("ASSET_EMBEDDINGS_FILENAME", "embeddings.csv") or "embeddings.csv").strip()
    if not fname.endswith(".csv"):
        fname = f"{fname}.csv"
    return fname

        embeddings_file = search_path / _embeddings_csv_filename()
```

**`.env` — after (excerpt)**

```env
ASSET_EMBEDDINGS_FILENAME=embeddingsMarco.csv
```

**`README.md` — sample env block**

Documents `ASSET_EMBEDDINGS_FILENAME=embeddings.csv` for new setups.

---

### 2026-03-21 — Workflow bypass: planner-dev skip + validator refinement cap

**Files:** `src/graph.py`, `main.py`, `.env`, `README.md`

**Problem:** Runs often ended in `GraphRecursionError` (Executor ↔ Validator loop): Roslyn validation fails without full Unity assemblies, `route` always sent failures back to Executor until the graph hit `recursion_limit`. Users iterating on the **Planner** needed the process to **finish cleanly** without editing Executor/Validator agent code.

**Why:** Handle two opt-in bypasses in **graph orchestration only** (plus CLI/env docs): (1) after a module plan is built, skip Asset Manager / Executor / Validator and mark the module complete; (2) after **N** failed validator→executor rounds, append a terminal history marker and route to `end` instead of looping.

---

**`src/graph.py` — `planner_node` (Case 1, after non-empty `implementation_steps`)**

New branch: if `XAGE_PLANNER_DEV_SKIP_IMPLEMENTATION` is `1` / `true` / `yes`, log, append `"Planner determined all tasks for module are complete"`, return state with `execution_plan` / `execution_plan_dict` preserved, `current_module` cleared, `completed_modules` / `completed_tasks` filled—**no** `asset_request` to Asset Manager.

**`src/graph.py` — `validator_node`**

Before appending `"Validator reported validation result to Executor"`, if `MAX_VALIDATOR_REFINEMENT_LOOPS` > 0, validation is not Success, and `prior_reports >= cap` (count of prior `"Validator reported validation result to Executor"` in history), append `"Validation refinement cap reached"`, push an explanatory string to `errors`, return (do **not** append the normal executor handoff line).

**`src/graph.py` — `route()`**

Insert rule: `("Validation refinement cap reached", "end")` **before** `("Validator reported validation result to Executor", "executor")` so the cap wins on `last_event`.

**`main.py` — after `parse_args`**

- `--planner-dev-skip-implementation` → sets `os.environ["XAGE_PLANNER_DEV_SKIP_IMPLEMENTATION"] = "1"`.
- `--max-validator-loops N` → sets `os.environ["MAX_VALIDATOR_REFINEMENT_LOOPS"]` (0 = unlimited when set explicitly from CLI).

**`.env` — new section (commented examples)**

`# XAGE_PLANNER_DEV_SKIP_IMPLEMENTATION=1` and `# MAX_VALIDATOR_REFINEMENT_LOOPS=1` under “Workflow bypass”.

**`README.md`**

New subsection *When the run never finishes (Executor ↔ Validator loop)* with table + example commands.

---

### 2026-03-21 — Planner artifacts on disk (`artifacts/planner/<run_id>/`)

**Files:** `src/utils/planner_artifacts.py`, `src/agents/planner.py`, `src/graph.py`, `README.md`

**Problem:** Only `artifacts/graph_execution_log.json` captured high-level graph I/O; there was no dedicated dump of **per-duty** planner inputs (orchestrator module, module brief, template text), **raw LLM responses**, parsed JSON, and downstream planner steps (prepare executor, advance task, dev skip).

**Why:** Add `write_planner_artifact()` keyed by `graph_execution_logger.run_id`, record duty traces inside `PlannerAgent.create_execution_plan` (after each duty), and emit extra JSON from `planner_node` for dev-skip / prepare-executor / advance transitions. Large template blobs use `maybe_truncate()` (~100k chars) with truncation metadata.

---

**`src/utils/planner_artifacts.py` — new**

- `planner_run_dir()` → `artifacts/planner/<run_id>/`
- `write_planner_artifact(filename, payload)`; `maybe_truncate()` for template strings.

**`src/agents/planner.py`**

- `create_execution_plan(..., orchestrator_module=...)`; `self._planner_trace` reset each run; `define_scene_hierarchy` / `decompose_steps` fill `duty1_*` / `duty2_*` with inputs, `raw_llm_response`, parsed output, fallback/parse/invoke flags.
- End of `create_execution_plan`: `module_<id>_create_plan.json` with orchestrator payload, full `final_execution_plan`.

**`src/graph.py`**

- Passes `orchestrator_module=state.get("current_module")` into `create_execution_plan`.
- Optional writes: `module_*_dev_skip.json`, `module_*_prepare_executor_task_*.json`, `module_*_advance_*.json`.

**`README.md`**

- *Inspecting Agent Outputs* updated: graph log + `artifacts/planner/` layout; project tree mentions `planner/<run_id>/`.

---

### 2026-03-21 — Markdown mirrors for all `artifacts/**/*.json` (`artifacts_readable/`)

**Files:** `src/utils/readable_artifacts.py`, `src/utils/graph_logger.py`, `src/utils/planner_artifacts.py`, `.gitignore`, `README.md`

**Problem:** JSON logs are complete but hard to scan for humans.

**Why:** After each write of JSON under `artifacts/`, emit a parallel **Markdown** file under **`artifacts_readable/`** with the **same relative path** (`.json` → `.md`). `graph_execution_log.json` uses a tailored layout (summary table + per-node sections + fenced JSON for inputs/outputs). Other files use top-level key sections with pretty JSON blocks. Large blobs capped with a truncation note. **`artifacts_readable/`** is gitignored. Backfill: `python -m src.utils.readable_artifacts`.

---

(Add new sections after the last `---` in Entries, or insert by date. This log keeps **earliest fixes at the top** of Entries.)

---

### 2026-03-28 — Bug fixes from first 3-layer planner run

**Files:** `src/graph.py`, `src/agents/asset_manager.py`, `src/utils/cleaning.py`

**Problem:** Three bugs surfaced on the first run of the new 3-layer planner.

---

**`src/graph.py` — before**
```python
num_tasks = len(execution_plan_dict.get("implementation_tasks", []))
```
**`src/graph.py` — after**
```python
num_tasks = len(execution_plan_dict.get("implementation_steps", []))
```
Wrong key caused the log to always show `Tasks: 0`.

---

**`src/agents/asset_manager.py` — before**
```python
for resource in resources:
    resource_type = resource.get("type", "").lower().strip()
```
**`src/agents/asset_manager.py` — after**
```python
for resource in resources:
    if isinstance(resource, str):
        resource = {"name": resource, "type": "3d model"}
    resource_type = resource.get("type", "").lower().strip()
```
LLM sometimes returns `required_assets` as a list of strings instead of dicts. The missing `isinstance` guard caused `AttributeError: 'str' object has no attribute 'get'` and crashed the workflow.

---

**`src/utils/cleaning.py` — before**

Single-strategy JSON extractor using a greedy `.*` regex; logged full tracebacks via `logger.exception`.

**`src/utils/cleaning.py` — after**

Added `_extract_balanced_json()` helper (char-by-char balanced-brace scanner that respects string literals). JSON branch now tries three strategies in order: ` ```json ` fence → generic fence → balanced-brace scan. Changed `logger.exception` → `logger.warning` (no more traceback noise).

---

### 2026-03-28 — Implement XAGE_PLANNER_DEV_SKIP_IMPLEMENTATION

**Files:** `src/graph.py`

**Problem:** `XAGE_PLANNER_DEV_SKIP_IMPLEMENTATION=1` was set in `.env` and documented in the changelog but the code that reads it was never added to `graph.py`. Setting it had no effect.

**Why:** Add the env-var check in `planner_node` Case 1, immediately after the plan is built. When active, skip Asset Manager / Executor / Validator entirely, mark the module complete, and route back to the Orchestrator.

---

**`src/graph.py` — after (inside `planner_node` Case 1)**

```python
dev_skip_flag = os.getenv("XAGE_PLANNER_DEV_SKIP_IMPLEMENTATION", "").strip().lower()
if dev_skip_flag in ("1", "true", "yes"):
    print("  ⚡ DEV SKIP: skipping implementation ...")
    # marks module complete, clears current_module, sets global_setup_done=True
    history.append("Planner determined all tasks for module are complete")
    return { ... }  # routes back to Orchestrator, no Asset Manager
```

---

### 2026-03-28 — Launch script `run_xage.sh`

**Files:** `run_xage.sh` (new, repo root)

**Problem:** The workflow was launched with `nohup python main.py ...` from `repo/`, but `main.py` lives in `repo/xage/`, causing `No such file or directory`.

**Why:** Create a small shell script at the repo root that always `cd`s into `repo/xage/` before launching, auto-generates a timestamped log filename, and runs in the background with `nohup`.

```bash
./run_xage.sh assets/001_sorting_wasted_automotive_batteries.pdf
./run_xage.sh assets/001_sorting_wasted_automotive_batteries.pdf --debug
```

---

### 2026-03-28 — Layer 3: split into 4 focused LLM calls to fix JSON truncation

**Files:** `src/prompts/planner_prompts.py`, `src/agents/planner.py`

**Problem:** `plan_step_tasks()` made a single LLM call asking for all 4 sub-duty tasks at once. For complex steps the output was regularly truncated mid-JSON, causing 5 parse failures across 4 modules in run 1. All 4 tasks fell back to generic placeholders.

**Why:** Split into 4 focused calls — one per sub-duty — so each call produces a small, well-bounded JSON (one task only). Result: 0 parse failures in run 2.

---

**`src/prompts/planner_prompts.py` — before**

One prompt pair (`PLANNER_STEP_TASKS_SYSTEM_PROMPT` / `PLANNER_STEP_TASKS_INPUT_PROMPT`) asking the LLM to return all 4 tasks in a single response.

**`src/prompts/planner_prompts.py` — after**

Four focused prompt pairs added (kept old prompt for reference):
- `PLANNER_SUBDTY_INSTANTIATE_SYSTEM_PROMPT` / `_INPUT_PROMPT`
- `PLANNER_SUBDTY_LOGIC_SYSTEM_PROMPT` / `_INPUT_PROMPT`
- `PLANNER_SUBDTY_EVENTS_SYSTEM_PROMPT` / `_INPUT_PROMPT`
- `PLANNER_SUBDTY_EVALUATION_SYSTEM_PROMPT` / `_INPUT_PROMPT`

Each returns `{"task": {...}}` — a single task dict.

**`src/agents/planner.py` — before**

```python
def plan_step_tasks(...) -> dict:
    # one LLM call → {"step_tasks": [task1, task2, task3, task4]}
```

**`src/agents/planner.py` — after**

```python
def _call_subdty(...)      # shared LLM invoke + parse + fallback helper
def _plan_instantiate(...) # sub-duty 1
def _plan_logic(...)       # sub-duty 2
def _plan_events(...)      # sub-duty 3
def _plan_evaluation(...)  # sub-duty 4

def plan_step_tasks(...):
    # calls all 4, assembles {"step_tasks": [...], "new_template_proposals": []}
```

Trade-off: ~4× more LLM calls per step (run time ~1h 54min vs ~1h 4min).

---

### 2026-03-28 — Layer 1 LLM call skipped on modules 2+

**Files:** `src/agents/planner.py`

**Problem:** `plan_global_setup()` (Layer 1) was called for every module even though `include_global_setup=False` already excluded those tasks from the flat execution list. This wasted one LLM call per extra module.

**Why:** Guard the LLM call with the existing `include_global_setup` flag so it is only invoked for the first module.

---

**`src/agents/planner.py` — before**

```python
# Layer 1 always called regardless of flag
print("  🌍 Layer 1: Planning Global Setup...")
layer1 = self.plan_global_setup(module_brief=module_description)
```

**`src/agents/planner.py` — after**

```python
if include_global_setup:
    print("  🌍 Layer 1: Planning Global Setup...")
    layer1 = self.plan_global_setup(module_brief=module_description)
else:
    print("  🌍 Layer 1: Skipped (already done for this session)")
    layer1 = {"global_setup_tasks": []}
```

---

### 2026-03-27 — Planner restructured into 3-layer Execution Plan

**Files:** `src/agents/planner.py`, `src/prompts/planner_prompts.py`, `src/graph.py`

**Problem:** The Planner produced a single flat list of `implementation_steps` with no structural distinction between one-time scene setup, per-module scaffolding, and per-step logic. This made it impossible to control execution scope (e.g. skipping global setup on subsequent modules) and the decomposition did not reflect the actual Unity development pattern.

**Why:** Restructure the Planner around three execution scopes that mirror the real Unity workflow:
- **Layer 1 (global)** — runs once per XAGE session: instantiate scenery, create Exercise Wrapper, create Module List Wrapper (`MultiProcessStep`).
- **Layer 2 (per module)** — runs once per module: create Module Wrapper (`ProcessStep`), add it to the Modules List.
- **Layer 3 (per step)** — runs per training step with four ordered sub-duties: instantiate visible objects, add exercise module logic, bind logic events, add exercise evaluation.

The output keeps a flat `implementation_steps` list so the graph loop is unchanged, but also exposes the structured `layers` dict for inspection. Layer 1 is automatically skipped on modules after the first via a new `global_setup_done` state flag.

---

**`src/prompts/planner_prompts.py` — before**

Two duties: `PLANNER_HIERARCHY_*` (scene hierarchy, disabled) and `PLANNER_DECOMPOSE_*` (flat step decomposition).

**`src/prompts/planner_prompts.py` — after**

Six new prompts (system + input per layer) added above the legacy prompts:
- `PLANNER_GLOBAL_SETUP_SYSTEM_PROMPT` / `PLANNER_GLOBAL_SETUP_INPUT_PROMPT`
- `PLANNER_MODULE_SETUP_SYSTEM_PROMPT` / `PLANNER_MODULE_SETUP_INPUT_PROMPT`
- `PLANNER_STEP_TASKS_SYSTEM_PROMPT` / `PLANNER_STEP_TASKS_INPUT_PROMPT`

Layer 3 prompt enforces exactly four sub-duty tasks per step (instantiate, logic, events, evaluation) with their specific sub-fields (`spawn_3d_models`, `exercise_steps`, `step_event_handlers`, etc.).

---

**`src/agents/planner.py` — before**

```python
def define_scene_hierarchy(...)  # Duty 1 – commented out in create_execution_plan
def decompose_step(...)           # Duty 2 – flat ≤5 sub-steps
def create_execution_plan(...)    # Returned: overview, implementation_steps, new_template_proposals
```

**`src/agents/planner.py` — after**

```python
def plan_global_setup(...)    # Layer 1 – 3 fixed global tasks
def plan_module_setup(...)    # Layer 2 – 2 fixed module tasks
def plan_step_tasks(...)      # Layer 3 – 4 sub-duty tasks per step

def create_execution_plan(..., include_global_setup: bool = True)
# Returns:
# {
#   "overview": "...",
#   "layers": {
#     "layer_1_global_setup": [...],
#     "layer_2_per_module": [...],
#     "layer_3_per_step": [{ "step_id": ..., "tasks": [...] }, ...]
#   },
#   "implementation_steps": [...],   # flat ordered list, layer tag on each item
#   "new_template_proposals": [...]
# }
```

Fallback methods added for all three layers (`_fallback_global_setup`, `_fallback_module_setup`, `_fallback_step_tasks`).

---

**`src/graph.py` — before**

```python
class WorkflowState(TypedDict, total=False):
    # no global_setup_done field

execution_plan_dict = planner.create_execution_plan(module_description=module_description)

# module complete return:
return { "completed_modules": ..., ... }

# run_workflow initial_state:
"validation_result": None,
"history": [],
```

**`src/graph.py` — after**

```python
class WorkflowState(TypedDict, total=False):
    global_setup_done: bool | None   # new field

global_setup_done = state.get("global_setup_done") or False
execution_plan_dict = planner.create_execution_plan(
    module_description=module_description,
    include_global_setup=not global_setup_done,
)

# module complete return now includes:
"global_setup_done": True,

# run_workflow initial_state:
"global_setup_done": False,
"history": [],
```
