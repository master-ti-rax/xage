import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ============================================================================
# Constants and Helpers
# ============================================================================

AGENT_OUTPUT_DIR = Path("artifacts/agent_outputs")


def _ensure_json_serializable(content: Any) -> Any:
    if isinstance(content, (dict, list, str, int, float, bool)) or content is None:
        return content
    if hasattr(content, "model_dump"):
        return content.model_dump()
    return {"content": str(content)}


def save_agent_output(agent_name: str, content: Any, extension: str | None = None, mode: str = "parsed") -> None:
	if mode == "raw":
		# Save raw output
		ext = extension or ".txt"
		try:
			AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
			file_path = AGENT_OUTPUT_DIR / f"{agent_name.lower()}_output_raw{ext}"
			with open(file_path, "w", encoding="utf-8") as f:
				f.write(str(content))
		except OSError:
			logger.exception("Failed to save raw output for %s", agent_name)
		return
	else:
		try:
			AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
			ext = extension or ".json"
			file_path = AGENT_OUTPUT_DIR / f"{agent_name.lower()}_output{ext}"
			if ext == ".json":
				payload = _ensure_json_serializable(content)
				file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
			else:
				file_path.write_text(str(content), encoding="utf-8")
		except OSError:
			logger.exception("Failed to save output for %s", agent_name)