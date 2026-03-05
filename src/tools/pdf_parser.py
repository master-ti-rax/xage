"""Generic PDF Educational Plan parser.

This module parses educational plans from PDF files by relying on structural
patterns (headings, bullet lists, module/step markers) instead of template-
specific hardcoded fields tied to a single sample file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pdfplumber


_MODULE_HEADING_PATTERN = re.compile(
	r"^(?:module|training\s+module|learning\s+module)\s+([0-9IVX]+)\s*[-–:]?\s*(.*)$",
	re.IGNORECASE,
)

_KNOWN_HEADINGS = {
	"xr_learning_activity_specification",
	"logo",
	"title",
	"language",
	"short_description",
	"long_description",
	"keywords",
	"expected_workload",
	"type_of_participation",
	"target_audience",
	"learning_objectives",
	"eqf_level",
	"isced_f_subject_areas",
	"esco_competences",
	"completion_criteria",
	"supervision_and_identity_verification",
	"assessment_requirement",
	"detailed_learning_design",
	"role_of_the_robot",
	"operational_parameters",
	"inspection_modes",
	"dismantling_modes",
	"inspection_cycle_duration",
	"dismantling_cycle_duration",
	"handling_bins",
	"material_routing_bins",
	"control_console",
	"process_menu",
	"status_panel",
	"training_script",
	"pedagogical_rationale",
	"learning_outcomes",
	"learning_flow",
	"learner_monitoring",
	"required_3d_assets",
	"required_assets",
}


@dataclass
class ParsedStep:
	"""A single instructional step inside a module."""

	step_id: str
	step_number: int
	title: str
	description: str

	def to_dict(self) -> dict[str, Any]:
		return {
			"step_id": self.step_id,
			"step_number": self.step_number,
			"title": self.title,
			"description": self.description,
		}


@dataclass
class ParsedModule:
	"""A parsed educational module."""

	module_id: int
	title: str
	duration_minutes: int | None = None
	pedagogical_rationale: str = ""
	learning_outcomes: list[str] = field(default_factory=list)
	learning_flow: dict[str, Any] = field(default_factory=dict)
	learner_monitoring: list[str] = field(default_factory=list)

	def to_dict(self) -> dict[str, Any]:
		return {
			"module_id": self.module_id,
			"title": self.title,
			"duration_minutes": self.duration_minutes,
			"pedagogical_rationale": self.pedagogical_rationale,
			"learning_outcomes": self.learning_outcomes,
			"learning_flow": self.learning_flow,
			"learner_monitoring": self.learner_monitoring,
		}


@dataclass
class ParsedEducationalPlan:
	"""Normalized parsed plan object."""

	metadata: dict[str, Any] = field(default_factory=dict)
	learning_objectives: list[str] = field(default_factory=list)
	classification: dict[str, Any] = field(default_factory=dict)
	completion_criteria: dict[str, Any] = field(default_factory=dict)
	detailed_learning_design: dict[str, Any] = field(default_factory=dict)
	modules: list[ParsedModule] = field(default_factory=list)
	required_3d_assets: dict[str, list[str]] = field(default_factory=dict)

	def to_dict(self) -> dict[str, Any]:
		training_script = {
			"overview": self.detailed_learning_design.get("overview", ""),
			"modules": [module.to_dict() for module in self.modules],
		}
		design = {
			**self.detailed_learning_design,
			"training_script": training_script,
		}

		return {
			"title": self.metadata.get("title") or "Educational Plan",
			"plans": [
				{
					"id": 1,
					"metadata": self.metadata,
					"learning_objectives": self.learning_objectives,
					"classification": self.classification,
					"completion_criteria": self.completion_criteria,
					"detailed_learning_design": design,
					"required_3d_assets": self.required_3d_assets,
				}
			],
		}


def extract_pdf_text(pdf_path: str | Path) -> str:
	"""Extract text from all pages in a PDF file."""
	path = Path(pdf_path)
	if not path.exists():
		raise FileNotFoundError(f"PDF file not found: {path}")

	pages: list[str] = []
	with pdfplumber.open(str(path)) as pdf:
		for page in pdf.pages:
			pages.append(page.extract_text(x_tolerance=2) or "")
	return "\n".join(pages)


def _clean_line(value: str) -> str:
	return re.sub(r"\s+", " ", value).strip()


def _normalize_key(value: str) -> str:
	lowered = re.sub(r"[^a-zA-Z0-9\s]", " ", value).lower()
	lowered = re.sub(r"\s+", " ", lowered).strip()
	return lowered.replace(" ", "_")


def _is_heading(line: str) -> bool:
	text = line.strip().rstrip(":")
	if not text:
		return False
	if text.startswith(("•", "-", "*", "–")):
		return False

	normalized = _normalize_key(text)
	if normalized in _KNOWN_HEADINGS:
		return True

	if _MODULE_HEADING_PATTERN.match(text):
		return True

	return False


def _split_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
	"""Split document lines into heading-based sections."""
	sections: list[tuple[str, list[str]]] = []
	current_heading = "document_intro"
	current_lines: list[str] = []

	for raw in lines:
		line = raw.strip()
		if not line:
			continue

		if _is_heading(line):
			if current_lines:
				sections.append((current_heading, current_lines))
			current_heading = line.rstrip(":")
			current_lines = []
			continue

		current_lines.append(line)

	if current_lines:
		sections.append((current_heading, current_lines))
	return sections


def _extract_bullets(lines: list[str]) -> list[str]:
	items: list[str] = []
	current: list[str] = []

	def flush() -> None:
		if current:
			items.append(_clean_line(" ".join(current)))
			current.clear()

	bullet_pattern = re.compile(r"^(?:[•\-*–]\s+|\d+\s*[\.)]\s+)")

	for line in lines:
		if bullet_pattern.match(line):
			flush()
			current.append(bullet_pattern.sub("", line).strip())
		elif current:
			current.append(line)
	flush()

	return [item for item in items if item]


def _extract_key_value_lines(lines: list[str]) -> dict[str, str]:
	"""Extract generic metadata fields from key-value style lines."""
	metadata: dict[str, str] = {}
	index = 0
	while index < len(lines):
		current = lines[index].strip()
		if not current:
			index += 1
			continue

		if ":" in current and len(current.split(":", 1)[0].split()) <= 8:
			left, right = current.split(":", 1)
			key = _normalize_key(left)
			value = _clean_line(right)
			if key and value:
				metadata[key] = value
			index += 1
			continue

		if _is_heading(current) and index + 1 < len(lines):
			nxt = lines[index + 1].strip()
			if nxt and not _is_heading(nxt):
				metadata[_normalize_key(current)] = _clean_line(nxt)
				index += 2
				continue

		index += 1
	return metadata


def _parse_classification(lines: list[str]) -> dict[str, Any]:
	entries: list[dict[str, str]] = []
	uris = re.findall(r"https?://\S+", "\n".join(lines))

	for item in _extract_bullets(lines):
		if re.search(r"\b\d{4}\b", item):
			code_match = re.search(r"\b(\d{4})\b", item)
			code = code_match.group(1) if code_match else ""
			label = item.replace(code, "", 1).strip(" -–:")
			entries.append({"code": code, "label": label})
		else:
			entries.append({"label": item})

	return {
		"taxonomy_entries": entries,
		"reference_uris": uris,
	}


def _parse_assets(lines: list[str]) -> dict[str, list[str]]:
	"""Parse assets/resources grouped by optional category labels."""
	grouped: dict[str, list[str]] = {}
	category = "general"
	grouped[category] = []

	for line in lines:
		stripped = line.strip()
		if not stripped:
			continue

		if stripped.endswith(":") and not stripped.startswith(("•", "-", "*", "–")):
			category = _normalize_key(stripped.rstrip(":")) or "general"
			grouped.setdefault(category, [])
			continue

		bullet_match = re.match(r"^(?:[•\-*–]\s+)(.+)$", stripped)
		if bullet_match:
			grouped.setdefault(category, []).append(_clean_line(bullet_match.group(1)))
			continue

		if ";" in stripped:
			tokens = [_clean_line(part) for part in stripped.split(";") if _clean_line(part)]
			if tokens:
				grouped.setdefault(category, []).extend(tokens)

	return {name: values for name, values in grouped.items() if values}


def _find_module_boundaries(lines: list[str]) -> list[tuple[int, int, str, str]]:
	"""Return (start, end, module_id_text, title) boundaries for module blocks."""
	module_regex = re.compile(
		_MODULE_HEADING_PATTERN.pattern,
		_MODULE_HEADING_PATTERN.flags,
	)

	starts: list[tuple[int, str, str]] = []
	for index, line in enumerate(lines):
		match = module_regex.match(line.strip())
		if not match:
			continue
		raw_id = (match.group(1) or "").strip()
		raw_title = (match.group(2) or "").strip()
		starts.append((index, raw_id, raw_title))

	boundaries: list[tuple[int, int, str, str]] = []
	for position, (start, raw_id, raw_title) in enumerate(starts):
		end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
		boundaries.append((start, end, raw_id, raw_title))
	return boundaries


def _roman_to_int(value: str) -> int | None:
	numerals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
	total = 0
	prev = 0
	for char in reversed(value.upper()):
		current = numerals.get(char)
		if current is None:
			return None
		if current < prev:
			total -= current
		else:
			total += current
			prev = current
	return total


def _parse_steps(module_id: int, lines: list[str]) -> list[ParsedStep]:
	step_regex = re.compile(
		r"^(?:step\s*)?([A-Za-z]*\d+(?:[_\.-]\d+)*)\s*[\)\].:–-]+\s*(.+)$",
		re.IGNORECASE,
	)
	numbered_regex = re.compile(r"^(\d+)\s*[\)\.]\s+(.+)$")
	# Matches prose step headings like "Orientation. A wall-mounted…" or "Equipment Check. …"
	prose_step_regex = re.compile(r"^([A-Z][A-Za-z\s]{2,40})\.\s+(.+)$")

	steps: list[ParsedStep] = []
	current_title = ""
	current_description: list[str] = []
	current_id = ""

	def flush() -> None:
		nonlocal current_title, current_description, current_id
		if not current_title:
			return
		step_number = len(steps) + 1
		sid = current_id or f"M{module_id}_S{step_number}"
		steps.append(
			ParsedStep(
				step_id=sid,
				step_number=step_number,
				title=_clean_line(current_title),
				description=_clean_line(" ".join(current_description)),
			)
		)
		current_title = ""
		current_description = []
		current_id = ""

	for line in lines:
		text = line.strip()
		if not text:
			continue

		match = step_regex.match(text)
		if match:
			flush()
			current_id = match.group(1)
			raw_title = match.group(2)
			# If the captured title itself looks like "ProseName. rest…", split it further
			prose_inner = prose_step_regex.match(raw_title)
			if prose_inner and len(prose_inner.group(1).split()) <= 5:
				current_title = prose_inner.group(1)
				current_description.append(prose_inner.group(2))
			else:
				current_title = raw_title
			continue

		number_match = numbered_regex.match(text)
		if number_match and len(text.split()) <= 16:
			flush()
			current_id = f"M{module_id}_S{number_match.group(1)}"
			current_title = number_match.group(2)
			continue

		# Prose heading pattern: short capitalised phrase followed by ". " and body text
		prose_match = prose_step_regex.match(text)
		if prose_match and len(prose_match.group(1).split()) <= 5:
			flush()
			current_id = f"M{module_id}_S{len(steps) + 1}"
			current_title = prose_match.group(1)
			current_description.append(prose_match.group(2))
			continue

		if current_title:
			current_description.append(text)

	flush()

	if steps:
		return steps

	bullets = _extract_bullets(lines)
	fallback_steps: list[ParsedStep] = []
	for index, item in enumerate(bullets, start=1):
		fallback_steps.append(
			ParsedStep(
				step_id=f"M{module_id}_S{index}",
				step_number=index,
				title=item,
				description=item,
			)
		)
	return fallback_steps


def _expand_inline_headings(lines: list[str]) -> list[str]:
	"""Split lines like 'Known Heading. Body text…' into two separate lines.

	Some PDFs write a section heading and its first sentence on one line separated
	by '. '.  This normalises them so that ``_split_sections`` can detect the
	heading and group the body under it correctly.
	"""
	inline_heading_re = re.compile(r"^([A-Z][A-Za-z\s]{2,50}?)\.\s+(.+)$")
	expanded: list[str] = []
	for line in lines:
		match = inline_heading_re.match(line.strip())
		if match:
			potential_heading = match.group(1).strip()
			if _normalize_key(potential_heading) in _KNOWN_HEADINGS:
				expanded.append(potential_heading)
				expanded.append(match.group(2).strip())
				continue
		expanded.append(line)
	return expanded


def _parse_modules(lines: list[str]) -> list[ParsedModule]:
	boundaries = _find_module_boundaries(lines)
	modules: list[ParsedModule] = []

	if not boundaries:
		return modules

	for fallback_id, (start, end, raw_id, raw_title) in enumerate(boundaries, start=1):
		module_lines = lines[start:end]
		parsed_id: int | None = None
		if raw_id.isdigit():
			parsed_id = int(raw_id)
		elif raw_id:
			parsed_id = _roman_to_int(raw_id)
		module_id = parsed_id or fallback_id

		header = module_lines[0] if module_lines else ""
		if raw_title:
			title = raw_title
		else:
			title = re.sub(r"^(?:module|training\s+module|learning\s+module)\s*[0-9IVX]*\s*[-–:]?\s*", "", header, flags=re.IGNORECASE).strip()
		title = title or f"Module {module_id}"

		duration_match = re.search(r"(\d+)\s*(?:minutes|minute|mins|min)\b", "\n".join(module_lines), re.IGNORECASE)
		duration = int(duration_match.group(1)) if duration_match else None

		# Split the module body into sub-sections using the known-headings mechanism
		# Pre-expand inline headings like "Pedagogical Rationale. Body text..." first
		expanded_lines = _expand_inline_headings(module_lines)
		sub_sections: dict[str, list[str]] = {}
		for section_heading, section_lines in _split_sections(expanded_lines):
			normalized = _normalize_key(section_heading)
			sub_sections.setdefault(normalized, []).extend(section_lines)

		# pedagogical_rationale
		rationale_lines = sub_sections.get("pedagogical_rationale", [])
		pedagogical_rationale = _clean_line(" ".join(rationale_lines))

		# learning_outcomes
		outcomes_lines = sub_sections.get("learning_outcomes", [])
		learning_outcomes: list[str] = _extract_bullets(outcomes_lines)
		if not learning_outcomes:
			learning_outcomes = [_clean_line(l) for l in outcomes_lines if l.strip()]

		# learning_flow – parse steps from the dedicated section; fall back to full block
		flow_lines = sub_sections.get("learning_flow", [])
		steps = _parse_steps(module_id, flow_lines) if flow_lines else _parse_steps(module_id, expanded_lines)

		# learner_monitoring
		monitoring_lines = sub_sections.get("learner_monitoring", [])
		monitoring: list[str] = _extract_bullets(monitoring_lines)
		if not monitoring:
			monitoring = [_clean_line(l) for l in monitoring_lines if l.strip()]

		modules.append(
			ParsedModule(
				module_id=module_id,
				title=_clean_line(title),
				duration_minutes=duration,
				pedagogical_rationale=pedagogical_rationale,
				learning_outcomes=list(dict.fromkeys(learning_outcomes)),
				learning_flow={
					"description": "Implementation flow extracted from module body.",
					"steps": [step.to_dict() for step in steps],
				},
				learner_monitoring=list(dict.fromkeys(monitoring)),
			)
		)

	return modules


def parse_educational_plan_pdf(pdf_path: str | Path) -> dict[str, Any]:
	"""Parse an educational plan PDF into normalized JSON.

	The parser is intentionally structure-driven and resilient to document
	wording differences by detecting headings, bullet lists, modules, and steps
	using generic patterns.
	"""
	path = Path(pdf_path)
	text = extract_pdf_text(path)
	lines = [_clean_line(line) for line in text.splitlines() if _clean_line(line)]

	sections = _split_sections(lines)

	metadata: dict[str, Any] = {
		"source_file": path.name,
	}
	if lines:
		metadata.setdefault("document_type", lines[0])

	metadata.update(_extract_key_value_lines(lines))

	# Generic heading-value fallback for common top-level descriptors
	for idx, line in enumerate(lines[:-1]):
		if _normalize_key(line) in {
			"title",
			"language",
			"short_description",
			"long_description",
			"keywords",
			"expected_workload",
			"type_of_participation",
			"target_audience",
		}:
			nxt = lines[idx + 1]
			if nxt and not _is_heading(nxt):
				metadata[_normalize_key(line)] = nxt

	if "title" not in metadata:
		for heading, content in sections:
			if heading.lower() == "title" and content:
				metadata["title"] = content[0]
				break

	learning_objectives: list[str] = []
	classification_lines: list[str] = []
	completion_lines: list[str] = []
	detailed_design_sections: dict[str, str] = {}
	assets_lines: list[str] = []

	for heading, content in sections:
		normalized = _normalize_key(heading)
		heading_lower = heading.lower()

		if any(token in heading_lower for token in ("objective", "outcome", "goal", "competenc")):
			learning_objectives.extend(_extract_bullets(content))
			continue

		if any(token in heading_lower for token in ("classification", "isced", "esco", "taxonomy")):
			classification_lines.extend(content)
			continue

		if any(token in heading_lower for token in ("completion", "assessment", "supervision", "criteria")):
			completion_lines.extend(content)
			continue

		if any(token in heading_lower for token in ("asset", "resource", "equipment", "material", "tool")):
			assets_lines.extend(content)
			continue

		if any(token in heading_lower for token in ("design", "workflow", "procedure", "operation", "robot", "console")):
			detailed_design_sections[normalized] = _clean_line(" ".join(content))

	modules = _parse_modules(lines)
	if not modules:
		raise ValueError(
			"Unable to parse modules from PDF. Expected explicit module headings like 'Module 1 - ...'."
		)

	completion_criteria = {
		"summary": _clean_line(" ".join(completion_lines)) if completion_lines else "",
		"items": _extract_bullets(completion_lines),
	}

	plan = ParsedEducationalPlan(
		metadata=metadata,
		learning_objectives=list(dict.fromkeys(learning_objectives)),
		classification=_parse_classification(classification_lines),
		completion_criteria=completion_criteria,
		detailed_learning_design={
			"overview": detailed_design_sections.get("detailed_learning_design", ""),
			"sections": detailed_design_sections,
		},
		modules=modules,
		required_3d_assets=_parse_assets(assets_lines),
	)
	return plan.to_dict()


def get_primary_plan(educational_plan: dict[str, Any]) -> dict[str, Any]:
	"""Return the primary parsed plan object from the normalized payload."""
	plans = educational_plan.get("plans")
	if not isinstance(plans, list) or not plans:
		raise ValueError("Educational plan is invalid: missing non-empty 'plans' list.")

	primary = plans[0]
	if not isinstance(primary, dict):
		raise ValueError("Educational plan is invalid: first entry in 'plans' must be an object.")
	return primary


def segment_educational_plan(educational_plan: dict[str, Any]) -> list[dict[str, Any]]:
	"""Return the module list from a parsed educational plan.

	This is a deterministic API that extracts segmented modules from the parser
	output schema, used by the Orchestrator duty #1.
	"""
	primary_plan = get_primary_plan(educational_plan)
	detailed = primary_plan.get("detailed_learning_design")
	if not isinstance(detailed, dict):
		raise ValueError("Educational plan is invalid: missing 'detailed_learning_design'.")

	training_script = detailed.get("training_script")
	if not isinstance(training_script, dict):
		raise ValueError("Educational plan is invalid: missing 'training_script'.")

	modules = training_script.get("modules")
	if not isinstance(modules, list):
		raise ValueError("Educational plan is invalid: 'training_script.modules' must be a list.")

	clean_modules: list[dict[str, Any]] = []
	for module in modules:
		if isinstance(module, dict):
			clean_modules.append(module)

	if not clean_modules:
		raise ValueError("Educational plan contains no valid modules for orchestration.")

	return clean_modules


def load_educational_plan(path: str | Path) -> dict[str, Any]:
	"""Load and parse an educational plan from PDF only."""
	plan_path = Path(path)
	if not plan_path.exists():
		raise FileNotFoundError(f"Educational plan file not found: {plan_path}")

	if plan_path.suffix.lower() != ".pdf":
		raise ValueError(
			"Unsupported file format. Only PDF educational plans are supported."
		)

	return parse_educational_plan_pdf(plan_path)


__all__ = [
	"ParsedStep",
	"ParsedModule",
	"ParsedEducationalPlan",
	"extract_pdf_text",
	"parse_educational_plan_pdf",
	"get_primary_plan",
	"segment_educational_plan",
	"load_educational_plan",
]
