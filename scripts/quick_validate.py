#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = ROOT / "skills" / "thinking-clarity"
CONTRACT_CASES_PATH = ROOT / "scripts" / "validation_cases.json"
TRIGGER_CASES_PATH = ROOT / "scripts" / "trigger_cases.json"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
AGENT_PATH = SKILL_ROOT / "agents" / "openai.yaml"
WORKFLOW_PATHS = {
    "clarify": SKILL_ROOT / "workflows" / "clarify.md",
    "deconstruct": SKILL_ROOT / "workflows" / "deconstruct.md",
    "simplify": SKILL_ROOT / "workflows" / "simplify.md",
    "decide": SKILL_ROOT / "workflows" / "decide.md",
}

CONTRACT_REQUIRED_KEYS = {
    "category",
    "id",
    "prompt",
    "case_type",
    "should_trigger",
    "expected_workflow",
    "expected_mode",
    "required_fields",
    "failure_risk",
    "why_this_case_exists",
    "routing_expectation",
}
TRIGGER_REQUIRED_KEYS = {
    "category",
    "id",
    "prompt",
    "case_type",
    "should_trigger",
    "expected_effects",
    "disallowed_effects",
    "failure_risk",
    "why_this_case_exists",
}
VALID_CASE_TYPES = {
    "clean_trigger",
    "messy_trigger",
    "boundary_stress",
    "adjacent_skill_false_positive",
    "non_trigger",
}
VALID_MODES = {"Quick Reframe", "Structured Analysis", "Pressure Test", "none"}
VALID_ROUTING_EXPECTATIONS = {"primary", "adjacent", "should_not_win"}
VALID_WORKFLOWS = set(WORKFLOW_PATHS)
VALID_SEQUENCES = {
    "clarify",
    "deconstruct",
    "simplify",
    "decide",
    "clarify>deconstruct",
    "clarify>deconstruct>simplify",
    "clarify>deconstruct>decide",
    "clarify>deconstruct>simplify>decide",
    "simplify>decide",
    "deconstruct>simplify",
    "deconstruct>decide",
    "deconstruct>simplify>decide",
}
WORKFLOW_ALIASES = {
    "Clarify": "clarify",
    "Deconstruct": "deconstruct",
    "Simplify": "simplify",
    "Decide": "decide",
}
CATEGORY_ALIASES = {
    "ai-system-design": "ai_system_design",
    "low-risk": "low_risk",
    "direct-answer": "direct_answer",
}
FIELD_ALIASES = {
    "surface question": "surface_question",
    "real goal": "real_goal",
    "reframed question": "reframed_question",
    "what must be preserved": "what_must_be_preserved",
    "options or moving parts": "options_or_moving_parts",
    "decision-relevant facts": "decision_relevant_facts",
    "hard constraints": "hard_constraints",
    "soft constraints": "soft_constraints",
    "recommendation": "recommendation",
    "next move": "next_move",
    "components": "components",
    "causal structure": "causal_structure",
    "what can be removed": "what_can_be_removed",
    "simplest sufficient option": "simplest_sufficient_option",
    "claim under test": "claim_under_test",
    "weak assumptions": "weak_assumptions",
    "missing evidence or contradiction": "missing_evidence_or_contradiction",
    "what survives scrutiny": "what_survives_scrutiny",
    "what is now clear": "what_is_now_clear",
    "best current recommendation": "recommendation",
    "main tradeoff or risk": "main_tradeoff_or_risk",
}
VALID_FIELDS = {
    "surface_question",
    "real_goal",
    "reframed_question",
    "what_must_be_preserved",
    "options_or_moving_parts",
    "decision_relevant_facts",
    "hard_constraints",
    "soft_constraints",
    "recommendation",
    "next_move",
    "components",
    "causal_structure",
    "what_can_be_removed",
    "simplest_sufficient_option",
    "claim_under_test",
    "weak_assumptions",
    "missing_evidence_or_contradiction",
    "what_survives_scrutiny",
    "what_is_now_clear",
    "main_tradeoff_or_risk",
}
WORKFLOW_ALLOWED_FIELDS = {
    "clarify": {
        "surface_question",
        "real_goal",
        "reframed_question",
        "next_move",
    },
    "deconstruct": {
        "real_goal",
        "components",
        "decision_relevant_facts",
        "hard_constraints",
        "soft_constraints",
        "causal_structure",
        "recommendation",
        "next_move",
    },
    "simplify": {
        "what_must_be_preserved",
        "options_or_moving_parts",
        "what_can_be_removed",
        "simplest_sufficient_option",
        "recommendation",
        "next_move",
        "real_goal",
        "hard_constraints",
        "soft_constraints",
        "decision_relevant_facts",
    },
    "decide": {
        "what_is_now_clear",
        "recommendation",
        "main_tradeoff_or_risk",
        "next_move",
        "real_goal",
        "hard_constraints",
        "soft_constraints",
        "decision_relevant_facts",
        "reframed_question",
        "claim_under_test",
        "weak_assumptions",
        "missing_evidence_or_contradiction",
        "what_survives_scrutiny",
    },
}
MODE_REQUIRED_FIELDS = {
    "Quick Reframe": {"real_goal", "reframed_question", "next_move"},
    "Structured Analysis": {"recommendation", "next_move"},
    "Pressure Test": {
        "claim_under_test",
        "weak_assumptions",
        "missing_evidence_or_contradiction",
        "what_survives_scrutiny",
        "next_move",
    },
}
DOC_EXPECTATIONS = {
    SKILL_PATH: [
        "## Workflow Routing",
        "## Response Modes",
        "## Output Contract",
        "soft constraints",
        "next move",
    ],
    WORKFLOW_PATHS["clarify"]: [
        "## Output format",
        "reframed question",
        "next move",
    ],
    WORKFLOW_PATHS["deconstruct"]: [
        "## Output format",
        "hard constraints",
        "soft constraints",
        "next move",
    ],
    WORKFLOW_PATHS["simplify"]: [
        "## Output format",
        "what must be preserved",
        "recommendation",
        "next move",
    ],
    WORKFLOW_PATHS["decide"]: [
        "## Output format",
        "best current recommendation",
        "main tradeoff or risk",
        "next move",
    ],
    AGENT_PATH: [
        "Start from the workflow that best matches the current problem shape",
        "soft constraints",
        "working judgment and an immediate next move",
    ],
}
REQUIRED_NON_TRIGGER_CATEGORIES = {
    "debugging",
    "brainstorming",
    "execution",
    "factual",
    "direct_answer",
    "low_risk",
}
REQUIRED_TRIGGER_CATEGORIES = {"technical", "product", "ai_system_design"}
DISALLOWED_SKILL_PACKAGE_PATHS = [
    "scripts",
    "tests",
    "pyproject.toml",
    "uv.lock",
    ".github",
]


def load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_docs() -> None:
    for path, fragments in DOC_EXPECTATIONS.items():
        if not path.exists():
            raise ValueError(f"Required file missing: {path}")
        content = path.read_text(encoding="utf-8")
        missing = [fragment for fragment in fragments if fragment not in content]
        if missing:
            raise ValueError(
                f"{path.relative_to(ROOT)} missing expected fragments: {missing}"
            )


def validate_repository_layout() -> None:
    if not SKILL_ROOT.exists():
        raise ValueError(f"Installable skill package missing: {SKILL_ROOT.relative_to(ROOT)}")
    if (ROOT / "SKILL.md").exists():
        raise ValueError("Root SKILL.md should not exist; use skills/thinking-clarity/SKILL.md")
    for relative in DISALLOWED_SKILL_PACKAGE_PATHS:
        if (SKILL_ROOT / relative).exists():
            raise ValueError(
                f"{relative} should stay outside the installable skill package"
            )


def split_workflow_sequence(value: str) -> list[str]:
    return value.split(">") if value else []


def normalize_workflow(value: str) -> str:
    if value == "none":
        return value
    parts = [part.strip() for part in value.split("->")]
    normalized = [WORKFLOW_ALIASES.get(part, part.lower()) for part in parts]
    return ">".join(normalized)


def normalize_contract_case(case: dict) -> dict:
    normalized = dict(case)
    normalized["category"] = CATEGORY_ALIASES.get(case["category"], case["category"])
    normalized["expected_workflow"] = normalize_workflow(case["expected_workflow"])
    if case.get("acceptable_workflows"):
        normalized["acceptable_workflows"] = [
            normalize_workflow(value) for value in case["acceptable_workflows"]
        ]
    if case.get("acceptable_modes"):
        normalized["acceptable_modes"] = list(case["acceptable_modes"])
    normalized["required_fields"] = [
        FIELD_ALIASES.get(field, field) for field in case["required_fields"]
    ]
    return normalized


def normalize_trigger_case(case: dict) -> dict:
    normalized = dict(case)
    normalized["category"] = CATEGORY_ALIASES.get(case["category"], case["category"])
    return normalized


def validate_contract_case_shape(case: dict) -> None:
    missing = CONTRACT_REQUIRED_KEYS - set(case.keys())
    if missing:
        raise ValueError(
            f"Contract case {case.get('id', '<unknown>')} missing keys: {sorted(missing)}"
        )
    if case["case_type"] not in VALID_CASE_TYPES:
        raise ValueError(
            f"Contract case {case['id']} has invalid case_type: {case['case_type']}"
        )
    if case["expected_mode"] not in VALID_MODES:
        raise ValueError(
            f"Contract case {case['id']} has invalid expected_mode: {case['expected_mode']}"
        )
    if case["routing_expectation"] not in VALID_ROUTING_EXPECTATIONS:
        raise ValueError(
            f"Contract case {case['id']} has invalid routing_expectation: {case['routing_expectation']}"
        )
    if not isinstance(case["required_fields"], list):
        raise ValueError(
            f"Contract case {case['id']} has invalid required_fields: expected list"
        )
    if "acceptable_workflows" in case and not isinstance(case["acceptable_workflows"], list):
        raise ValueError(
            f"Contract case {case['id']} has invalid acceptable_workflows: expected list"
        )
    if "acceptable_modes" in case and not isinstance(case["acceptable_modes"], list):
        raise ValueError(
            f"Contract case {case['id']} has invalid acceptable_modes: expected list"
        )

    invalid_fields = sorted(set(case["required_fields"]) - VALID_FIELDS)
    if invalid_fields:
        raise ValueError(
            f"Contract case {case['id']} has unknown required_fields: {invalid_fields}"
        )


def validate_contract_trigger_case(case: dict) -> None:
    workflow = case["expected_workflow"]
    if workflow not in VALID_SEQUENCES:
        raise ValueError(
            f"Contract case {case['id']} has invalid expected_workflow: {workflow}"
        )

    steps = split_workflow_sequence(workflow)
    unknown_steps = [step for step in steps if step not in VALID_WORKFLOWS]
    if unknown_steps:
        raise ValueError(
            f"Contract case {case['id']} references unknown workflows: {unknown_steps}"
        )
    if not case["required_fields"]:
        raise ValueError(
            f"Contract case {case['id']} is a trigger case but has no required_fields"
        )

    allowed_fields = set()
    for step in steps:
        allowed_fields.update(WORKFLOW_ALLOWED_FIELDS[step])
    disallowed = sorted(set(case["required_fields"]) - allowed_fields)
    if disallowed:
        raise ValueError(
            f"Contract case {case['id']} requires fields not supported by {workflow}: {disallowed}"
        )

    missing_mode_fields = MODE_REQUIRED_FIELDS[case["expected_mode"]] - set(case["required_fields"])
    if missing_mode_fields:
        raise ValueError(
            f"Contract case {case['id']} is missing mode-required fields for {case['expected_mode']}: {sorted(missing_mode_fields)}"
        )

    if "next_move" not in case["required_fields"]:
        raise ValueError(f"Contract case {case['id']} must require next_move")
    if case["expected_mode"] == "Structured Analysis" and "recommendation" not in case["required_fields"]:
        raise ValueError(
            f"Contract case {case['id']} must require recommendation for Structured Analysis"
        )

    acceptable_workflows = case.get("acceptable_workflows") or []
    invalid_workflows = [value for value in acceptable_workflows if value not in VALID_SEQUENCES]
    if invalid_workflows:
        raise ValueError(
            f"Contract case {case['id']} has invalid acceptable_workflows: {invalid_workflows}"
        )
    if acceptable_workflows and workflow not in acceptable_workflows:
        raise ValueError(
            f"Contract case {case['id']} acceptable_workflows must include expected_workflow"
        )

    acceptable_modes = case.get("acceptable_modes") or []
    invalid_modes = [value for value in acceptable_modes if value not in VALID_MODES]
    if invalid_modes:
        raise ValueError(
            f"Contract case {case['id']} has invalid acceptable_modes: {invalid_modes}"
        )
    if acceptable_modes and case["expected_mode"] not in acceptable_modes:
        raise ValueError(
            f"Contract case {case['id']} acceptable_modes must include expected_mode"
        )


def validate_contract_non_trigger_case(case: dict) -> None:
    if case["expected_workflow"] != "none" or case["expected_mode"] != "none":
        raise ValueError(
            f"Contract case {case['id']} is non-trigger but expected_workflow/expected_mode are not 'none'"
        )
    if case["required_fields"]:
        raise ValueError(
            f"Contract case {case['id']} is non-trigger but required_fields is not empty"
        )
    if case["routing_expectation"] != "should_not_win":
        raise ValueError(
            f"Contract case {case['id']} is non-trigger but routing_expectation is not 'should_not_win'"
        )


def validate_contract_cases(cases: list[dict]) -> None:
    seen_ids: set[str] = set()
    for case in cases:
        validate_contract_case_shape(case)
        if case["id"] in seen_ids:
            raise ValueError(f"Duplicate contract case id: {case['id']}")
        seen_ids.add(case["id"])

        if case["should_trigger"]:
            validate_contract_trigger_case(case)
        else:
            validate_contract_non_trigger_case(case)


def validate_contract_coverage(cases: list[dict]) -> None:
    trigger_cases = [case for case in cases if case["should_trigger"]]
    non_trigger_cases = [case for case in cases if not case["should_trigger"]]

    covered_workflows = set()
    covered_modes = set()
    for case in trigger_cases:
        covered_workflows.update(split_workflow_sequence(case["expected_workflow"]))
        covered_modes.add(case["expected_mode"])

    missing_workflows = VALID_WORKFLOWS - covered_workflows
    if missing_workflows:
        raise ValueError(
            f"Missing contract trigger coverage for workflows: {sorted(missing_workflows)}"
        )

    missing_modes = {"Quick Reframe", "Structured Analysis", "Pressure Test"} - covered_modes
    if missing_modes:
        raise ValueError(
            f"Missing contract trigger coverage for modes: {sorted(missing_modes)}"
        )

    if not any(">" in case["expected_workflow"] for case in trigger_cases):
        raise ValueError("Need at least one contract trigger case with a multi-step workflow")
    if not any(case["expected_workflow"] == "decide" for case in trigger_cases):
        raise ValueError("Need at least one contract trigger case that goes direct to decide")
    if not any("soft_constraints" in case["required_fields"] for case in trigger_cases):
        raise ValueError("Need at least one contract trigger case that exercises soft_constraints")

    boundary_categories = {case["category"] for case in non_trigger_cases}
    missing_boundary_categories = REQUIRED_NON_TRIGGER_CATEGORIES - boundary_categories
    if missing_boundary_categories:
        raise ValueError(
            "Missing contract non-trigger boundary coverage for categories: "
            + str(sorted(missing_boundary_categories))
        )


def validate_trigger_case_shape(case: dict) -> None:
    missing = TRIGGER_REQUIRED_KEYS - set(case.keys())
    if missing:
        raise ValueError(
            f"Trigger case {case.get('id', '<unknown>')} missing keys: {sorted(missing)}"
        )
    if case["case_type"] not in VALID_CASE_TYPES:
        raise ValueError(
            f"Trigger case {case['id']} has invalid case_type: {case['case_type']}"
        )
    if not isinstance(case["expected_effects"], list) or not case["expected_effects"]:
        raise ValueError(
            f"Trigger case {case['id']} must have a non-empty expected_effects list"
        )
    if not isinstance(case["disallowed_effects"], list):
        raise ValueError(
            f"Trigger case {case['id']} has invalid disallowed_effects: expected list"
        )


def validate_trigger_cases(cases: list[dict]) -> None:
    seen_ids: set[str] = set()
    for case in cases:
        validate_trigger_case_shape(case)
        if case["id"] in seen_ids:
            raise ValueError(f"Duplicate trigger case id: {case['id']}")
        seen_ids.add(case["id"])


def validate_trigger_coverage(cases: list[dict]) -> None:
    positive = [case for case in cases if case["should_trigger"]]
    negative = [case for case in cases if not case["should_trigger"]]
    if not positive:
        raise ValueError("Need at least one positive trigger eval case")
    if not negative:
        raise ValueError("Need at least one negative trigger eval case")

    positive_categories = {case["category"] for case in positive}
    missing_positive_categories = REQUIRED_TRIGGER_CATEGORIES - positive_categories
    if missing_positive_categories:
        raise ValueError(
            "Missing positive trigger eval coverage for categories: "
            + str(sorted(missing_positive_categories))
        )

    negative_categories = {case["category"] for case in negative}
    missing_negative_categories = REQUIRED_NON_TRIGGER_CATEGORIES - negative_categories
    if missing_negative_categories:
        raise ValueError(
            "Missing negative trigger eval coverage for categories: "
            + str(sorted(missing_negative_categories))
        )


def summarize_contract_cases(cases: list[dict]) -> None:
    trigger_cases = [c for c in cases if c["should_trigger"]]
    non_trigger_cases = [c for c in cases if not c["should_trigger"]]
    print("Contract cases:")
    print(f"- total: {len(cases)}")
    print(f"- trigger: {len(trigger_cases)}")
    print(f"- non-trigger: {len(non_trigger_cases)}")
    print("- counts by workflow step:")
    workflow_counts = Counter()
    for case in trigger_cases:
        workflow_counts.update(split_workflow_sequence(case["expected_workflow"]))
    for key, value in sorted(workflow_counts.items()):
        print(f"  - {key}: {value}")
    print("- counts by mode:")
    for key, value in sorted(Counter(c["expected_mode"] for c in trigger_cases).items()):
        print(f"  - {key}: {value}")


def summarize_trigger_cases(cases: list[dict]) -> None:
    positive = [c for c in cases if c["should_trigger"]]
    negative = [c for c in cases if not c["should_trigger"]]
    print("Trigger eval cases:")
    print(f"- total: {len(cases)}")
    print(f"- should-trigger: {len(positive)}")
    print(f"- should-not-trigger: {len(negative)}")
    print("- counts by category:")
    for key, value in sorted(Counter(c["category"] for c in cases).items()):
        print(f"  - {key}: {value}")


def main() -> None:
    validate_repository_layout()
    validate_docs()

    contract_cases = [normalize_contract_case(case) for case in load_json(CONTRACT_CASES_PATH)]
    validate_contract_cases(contract_cases)
    validate_contract_coverage(contract_cases)

    trigger_cases = [normalize_trigger_case(case) for case in load_json(TRIGGER_CASES_PATH)]
    validate_trigger_cases(trigger_cases)
    validate_trigger_coverage(trigger_cases)

    print("PASS: repository layout check")
    print("PASS: documentation contract check")
    print("PASS: contract case schema check")
    print("PASS: contract coverage check")
    print("PASS: trigger case schema check")
    print("PASS: trigger coverage check")
    print()
    summarize_contract_cases(contract_cases)
    print()
    summarize_trigger_cases(trigger_cases)


if __name__ == "__main__":
    main()
