#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from codex_isolation import claude_home_environment, codex_home_environment

ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = ROOT / "skills" / "thinking-clarity"
CASES_PATH = ROOT / "scripts" / "validation_cases.json"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_CODEX_TIMEOUT = 180
DEFAULT_CLAUDE_TIMEOUT = 300
DEFAULT_RUNNER = "claude"
DEFAULT_CODEX_BIN = "codex"
DEFAULT_CODEX_REASONING_EFFORT = "medium"
DEFAULT_CLAUDE_BIN = "claude"
DEFAULT_CLAUDE_EFFORT = "medium"
VALID_BUNDLE_PROFILES = {"minimal", "balanced", "full"}
CLAUDE_EVAL_SYSTEM_PROMPT = (
    "Answer from the provided prompt and schema only. "
    "Do not inspect the workspace, repository, or files. "
    "Do not ask to inspect code or gather local context unless the prompt itself provides it."
)

WORKFLOW_ALIASES = {
    "Clarify": "clarify",
    "Deconstruct": "deconstruct",
    "Simplify": "simplify",
    "Decide": "decide",
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
CANONICAL_SECTION_KEYS = [
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
]
WORKFLOW_FILE_PATHS = {
    "clarify": SKILL_ROOT / "workflows" / "clarify.md",
    "deconstruct": SKILL_ROOT / "workflows" / "deconstruct.md",
    "simplify": SKILL_ROOT / "workflows" / "simplify.md",
    "decide": SKILL_ROOT / "workflows" / "decide.md",
}
BASE_BUNDLE_FILES = [
    ("SKILL.md", SKILL_ROOT / "SKILL.md"),
    ("agents/openai.yaml", SKILL_ROOT / "agents" / "openai.yaml"),
]


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_workflow(value: str) -> str:
    if value == "none":
        return value
    parts = [part.strip() for part in value.split("->")]
    normalized = [WORKFLOW_ALIASES.get(part, part.lower()) for part in parts]
    return ">".join(normalized)


def normalize_expected_case(case: dict) -> dict:
    normalized = dict(case)
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


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def extract_workflows(case: dict) -> list[str]:
    sequences = [case["expected_workflow"]] + list(case.get("acceptable_workflows") or [])
    workflows: list[str] = []
    for sequence in sequences:
        normalized = normalize_workflow(sequence)
        if normalized == "none":
            continue
        workflows.extend(part for part in normalized.split(">") if part)
    return unique_in_order(workflows)


def should_include_anti_patterns(case: dict) -> bool:
    return case["case_type"] in {"messy_trigger", "boundary_stress"} or (
        case.get("expected_mode") == "Pressure Test"
    )


def should_include_examples(case: dict, bundle_profile: str) -> bool:
    if bundle_profile == "full":
        return True
    if bundle_profile == "minimal":
        return False
    if not case["should_trigger"]:
        return False
    return case["case_type"] in {"messy_trigger", "boundary_stress"} or (
        case.get("expected_mode") == "Pressure Test"
    )


def build_skill_bundle(case: dict, bundle_profile: str) -> str:
    if bundle_profile not in VALID_BUNDLE_PROFILES:
        raise ValueError(f"Unknown bundle profile: {bundle_profile}")

    files = list(BASE_BUNDLE_FILES)
    if bundle_profile == "full":
        files.extend(
            [
                ("workflows/clarify.md", WORKFLOW_FILE_PATHS["clarify"]),
                ("workflows/deconstruct.md", WORKFLOW_FILE_PATHS["deconstruct"]),
                ("workflows/simplify.md", WORKFLOW_FILE_PATHS["simplify"]),
                ("workflows/decide.md", WORKFLOW_FILE_PATHS["decide"]),
                ("references/anti-patterns.md", SKILL_ROOT / "references" / "anti-patterns.md"),
                ("references/output-patterns.md", SKILL_ROOT / "references" / "output-patterns.md"),
                ("references/examples.md", SKILL_ROOT / "references" / "examples.md"),
            ]
        )
    else:
        for workflow in extract_workflows(case):
            files.append((f"workflows/{workflow}.md", WORKFLOW_FILE_PATHS[workflow]))

        if case["should_trigger"]:
            files.append(
                ("references/output-patterns.md", SKILL_ROOT / "references" / "output-patterns.md")
            )
        if should_include_anti_patterns(case):
            files.append(
                ("references/anti-patterns.md", SKILL_ROOT / "references" / "anti-patterns.md")
            )
        if should_include_examples(case, bundle_profile):
            files.append(("references/examples.md", SKILL_ROOT / "references" / "examples.md"))

    parts = []
    for label, path in unique_in_order([(label, str(path)) for label, path in files]):
        file_path = Path(path)
        parts.append(f"--- BEGIN {label} ---")
        parts.append(file_path.read_text(encoding="utf-8"))
        parts.append(f"--- END {label} ---")
    return "\n\n".join(parts)


def structured_output_schema(required_fields: list[str]) -> dict:
    section_keys = unique_in_order(
        [field for field in required_fields if field in CANONICAL_SECTION_KEYS]
    )
    section_properties = {
        key: {"type": ["string", "null"]} for key in section_keys
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "should_trigger": {"type": "boolean"},
            "workflow": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["clarify", "deconstruct", "simplify", "decide"],
                },
            },
            "response_mode": {
                "type": "string",
                "enum": [
                    "Quick Reframe",
                    "Structured Analysis",
                    "Pressure Test",
                    "none",
                ],
            },
            "boundary_reason": {"type": ["string", "null"]},
            "sections": {
                "type": "object",
                "additionalProperties": False,
                "properties": section_properties,
                "required": section_keys,
            },
            "final_answer": {"type": ["string", "null"]},
        },
        "required": [
            "should_trigger",
            "workflow",
            "response_mode",
            "boundary_reason",
            "sections",
            "final_answer",
        ],
    }


def openai_response_format(required_fields: list[str]) -> dict:
    return {
        "type": "json_schema",
        "name": "thinking_clarity_contract_eval",
        "strict": True,
        "schema": structured_output_schema(required_fields),
    }


def build_eval_rules() -> str:
    return """You are running a contract eval for the thinking-clarity skill.

Use the skill materials below as the source of truth.

Rules:
- Choose the lightest workflow that solves the current blockage.
- If the skill should not trigger, set should_trigger to false, workflow to an empty list, response_mode to "none", final_answer to null, and use boundary_reason to explain why.
- If the skill should trigger, set should_trigger to true, choose the workflow sequence, choose the response mode, populate only the relevant section fields, and provide a natural-language final_answer consistent with those sections.
- Do not skip clarify when the prompt is really about diagnosing what the actual problem is.
- Do not skip deconstruct when the answer depends on mechanism, root cause, or separating hard limits from softer pressure.
- Prefer Structured Analysis for scope, prioritization, sequencing, and architecture choices, even if the prompt mentions someone else's claim.
- Use Pressure Test only when claim scrutiny is the center of the answer.
- If you choose Quick Reframe, keep the answer narrow. If you are already weighing facts, constraints, or interventions, use Structured Analysis instead.
- If the workflow includes deconstruct, make components and causal structure explicit.
- Only populate section keys that are materially relevant to the answer.
- Do not invent workflows beyond clarify, deconstruct, simplify, decide.
- Keep workflow items lower-case.
- Keep section keys in snake_case exactly as required by the schema.
"""


def build_eval_prompt(skill_bundle: str, prompt: str) -> str:
    return f"""{build_eval_rules()}

Skill materials:

{skill_bundle}

User prompt:
{prompt}
"""


def build_openai_payload(model: str, skill_bundle: str, prompt: str, required_fields: list[str]) -> dict:
    return {
        "model": model,
        "instructions": build_eval_rules() + "\n\nSkill materials:\n\n" + skill_bundle,
        "input": prompt,
        "text": {"format": openai_response_format(required_fields)},
    }


def extract_output_text(response: dict) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    for item in response.get("output", []):
        if item.get("type") != "message" or item.get("role") != "assistant":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(
                content.get("text"), str
            ):
                return content["text"]

    raise ValueError("Could not find assistant output text in API response")


def parse_json_message(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return json.loads(stripped)


def call_openai(payload: dict, api_key: str, base_url: str, timeout: int) -> dict:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc


def summarize_process_output(text: str, limit: int = 1200) -> str:
    if not text:
        return ""
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    head = stripped[:400]
    tail = stripped[-700:]
    return head + "\n...\n" + tail


def normalize_claude_effort(effort: str) -> str:
    return {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "xhigh": "max",
    }[effort]


def build_codex_command(
    codex_bin: str,
    model: str | None,
    output_path: Path,
    reasoning_effort: str,
    schema_path: Path | None = None,
) -> list[str]:
    command = [
        codex_bin,
        "exec",
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--ephemeral",
        "--color",
        "never",
        "--output-last-message",
        str(output_path),
        "-C",
        str(ROOT),
        "-",
    ]
    if schema_path is not None:
        command[10:10] = ["--output-schema", str(schema_path)]
    if model:
        command[2:2] = ["--model", model]
    return command


def build_claude_command(
    claude_bin: str,
    model: str | None,
    prompt: str,
    effort: str,
    schema: dict | None = None,
    system_prompt: str | None = None,
) -> list[str]:
    command = [
        claude_bin,
        "-p",
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
        "--tools",
        "",
        "--setting-sources",
        "user",
        "--no-session-persistence",
        "--effort",
        normalize_claude_effort(effort),
    ]
    if model:
        command.extend(["--model", model])
    if system_prompt:
        command.extend(["--system-prompt", system_prompt])
    if schema is not None:
        command.extend(
            ["--json-schema", json.dumps(schema, separators=(",", ":"), ensure_ascii=False)]
        )
    command.append(prompt)
    return command


def run_codex_command(
    prompt: str,
    codex_bin: str,
    model: str | None,
    timeout: int,
    reasoning_effort: str,
    skill_environment: str,
    schema: dict | None = None,
) -> tuple[str, dict]:
    with codex_home_environment(skill_environment, install_skill=False) as env:
        with tempfile.TemporaryDirectory(prefix="thinking-clarity-eval-") as tmpdir:
            output_path = Path(tmpdir) / "last_message.txt"
            schema_path: Path | None = None
            if schema is not None:
                schema_path = Path(tmpdir) / "schema.json"
                schema_path.write_text(
                    json.dumps(schema, indent=2) + "\n",
                    encoding="utf-8",
                )

            cmd = build_codex_command(
                codex_bin=codex_bin,
                model=model,
                output_path=output_path,
                reasoning_effort=reasoning_effort,
                schema_path=schema_path,
            )
            try:
                completed = subprocess.run(
                    cmd,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(ROOT),
                    env=env,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(f"Codex CLI not found: {codex_bin}") from exc
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"Codex CLI timed out after {timeout}s") from exc

            if completed.returncode != 0:
                raise RuntimeError(
                    "Codex CLI failed with exit code "
                    f"{completed.returncode}\nSTDOUT:\n{summarize_process_output(completed.stdout)}"
                    f"\nSTDERR:\n{summarize_process_output(completed.stderr)}"
                )

            if not output_path.exists():
                raise RuntimeError(
                    "Codex CLI completed but did not write the final message file.\n"
                    f"STDOUT:\n{summarize_process_output(completed.stdout)}"
                    f"\nSTDERR:\n{summarize_process_output(completed.stderr)}"
                )

            return output_path.read_text(encoding="utf-8"), {
                "stdout_excerpt": summarize_process_output(completed.stdout),
                "stderr_excerpt": summarize_process_output(completed.stderr),
                "command": cmd,
                "skill_environment": skill_environment,
            }


def extract_claude_result(response: dict, schema: dict | None) -> str:
    if schema is not None and isinstance(response.get("structured_output"), dict):
        return json.dumps(response["structured_output"], ensure_ascii=False)
    result = response.get("result")
    if isinstance(result, str):
        return result
    raise ValueError("Could not find Claude result text in CLI response")


def run_claude_command(
    prompt: str,
    claude_bin: str,
    model: str | None,
    timeout: int,
    effort: str,
    skill_environment: str,
    schema: dict | None = None,
    system_prompt: str | None = None,
) -> tuple[str, dict]:
    with claude_home_environment(skill_environment, install_skill=False) as env:
        cmd = build_claude_command(
            claude_bin=claude_bin,
            model=model,
            prompt=prompt,
            effort=effort,
            schema=schema,
            system_prompt=system_prompt,
        )
        try:
            completed = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=str(ROOT),
                env=env,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"Claude CLI not found: {claude_bin}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Claude CLI timed out after {timeout}s") from exc

        if completed.returncode != 0:
            raise RuntimeError(
                "Claude CLI failed with exit code "
                f"{completed.returncode}\nSTDOUT:\n{summarize_process_output(completed.stdout)}"
                f"\nSTDERR:\n{summarize_process_output(completed.stderr)}"
            )

        parsed_stdout = json.loads(completed.stdout)
        return extract_claude_result(parsed_stdout, schema), {
            "stdout_excerpt": summarize_process_output(completed.stdout),
            "stderr_excerpt": summarize_process_output(completed.stderr),
            "command": cmd,
            "skill_environment": skill_environment,
            "usage": parsed_stdout.get("usage"),
            "total_cost_usd": parsed_stdout.get("total_cost_usd"),
        }


def is_present(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def score_case(expected: dict, actual: dict) -> dict:
    failed_checks: list[str] = []
    expected_should_trigger = expected["should_trigger"]
    actual_should_trigger = actual.get("should_trigger")

    if actual_should_trigger is not expected_should_trigger:
        failed_checks.append("should_trigger")

    actual_workflow = ">".join(actual.get("workflow", [])) if actual.get("workflow") else "none"
    acceptable_workflows = expected.get("acceptable_workflows") or [expected["expected_workflow"]]
    if actual_workflow not in acceptable_workflows:
        failed_checks.append("workflow")

    acceptable_modes = expected.get("acceptable_modes") or [expected["expected_mode"]]
    if actual.get("response_mode") not in acceptable_modes:
        failed_checks.append("response_mode")

    sections = actual.get("sections") or {}
    missing_required = [
        field for field in expected["required_fields"] if not is_present(sections.get(field))
    ]
    if missing_required:
        failed_checks.append("required_fields")

    if expected_should_trigger and not is_present(actual.get("final_answer")):
        failed_checks.append("final_answer")

    return {
        "passed": not failed_checks,
        "failed_checks": failed_checks,
        "missing_required_fields": missing_required,
        "actual_workflow": actual_workflow,
        "actual_mode": actual.get("response_mode"),
    }


def evaluate_case_openai(
    case: dict,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int,
    bundle_profile: str,
) -> dict:
    normalized_case = normalize_expected_case(case)
    skill_bundle = build_skill_bundle(normalized_case, bundle_profile=bundle_profile)
    payload = build_openai_payload(
        model=model,
        skill_bundle=skill_bundle,
        prompt=case["prompt"],
        required_fields=normalized_case["required_fields"],
    )
    started = time.time()
    raw_response = call_openai(
        payload=payload, api_key=api_key, base_url=base_url, timeout=timeout
    )
    elapsed_ms = int((time.time() - started) * 1000)
    parsed = parse_json_message(extract_output_text(raw_response))
    score = score_case(normalized_case, parsed)
    prompt_chars = len(build_eval_prompt(skill_bundle=skill_bundle, prompt=case["prompt"]))
    return {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "runner": "openai",
        "model": model,
        "bundle_profile": bundle_profile,
        "bundle_chars": len(skill_bundle),
        "prompt_chars": prompt_chars,
        "latency_ms": elapsed_ms,
        "usage": raw_response.get("usage"),
        "expected": {
            "should_trigger": normalized_case["should_trigger"],
            "workflow": normalized_case["expected_workflow"],
            "mode": normalized_case["expected_mode"],
            "required_fields": normalized_case["required_fields"],
        },
        "actual": parsed,
        "score": score,
    }


def evaluate_case_codex(
    case: dict,
    model: str | None,
    codex_bin: str,
    timeout: int,
    bundle_profile: str,
    reasoning_effort: str,
    skill_environment: str,
    include_logs: bool,
) -> dict:
    normalized_case = normalize_expected_case(case)
    skill_bundle = build_skill_bundle(normalized_case, bundle_profile=bundle_profile)
    prompt = build_eval_prompt(skill_bundle=skill_bundle, prompt=case["prompt"])
    started = time.time()
    raw_text, logs = run_codex_command(
        prompt=prompt,
        codex_bin=codex_bin,
        model=model,
        timeout=timeout,
        reasoning_effort=reasoning_effort,
        skill_environment=skill_environment,
        schema=structured_output_schema(normalized_case["required_fields"]),
    )
    elapsed_ms = int((time.time() - started) * 1000)
    parsed = parse_json_message(raw_text)
    score = score_case(normalized_case, parsed)
    result = {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "runner": "codex",
        "model": model,
        "reasoning_effort": reasoning_effort,
        "skill_environment": skill_environment,
        "bundle_profile": bundle_profile,
        "bundle_chars": len(skill_bundle),
        "prompt_chars": len(prompt),
        "latency_ms": elapsed_ms,
        "usage": None,
        "expected": {
            "should_trigger": normalized_case["should_trigger"],
            "workflow": normalized_case["expected_workflow"],
            "mode": normalized_case["expected_mode"],
            "required_fields": normalized_case["required_fields"],
        },
        "actual": parsed,
        "score": score,
    }
    if include_logs:
        result["logs"] = logs
    return result


def evaluate_case_claude(
    case: dict,
    model: str | None,
    claude_bin: str,
    timeout: int,
    bundle_profile: str,
    effort: str,
    skill_environment: str,
    include_logs: bool,
) -> dict:
    normalized_case = normalize_expected_case(case)
    skill_bundle = build_skill_bundle(normalized_case, bundle_profile=bundle_profile)
    prompt = build_eval_prompt(skill_bundle=skill_bundle, prompt=case["prompt"])
    started = time.time()
    raw_text, logs = run_claude_command(
        prompt=prompt,
        claude_bin=claude_bin,
        model=model,
        timeout=timeout,
        effort=effort,
        skill_environment=skill_environment,
        schema=structured_output_schema(normalized_case["required_fields"]),
        system_prompt=CLAUDE_EVAL_SYSTEM_PROMPT,
    )
    elapsed_ms = int((time.time() - started) * 1000)
    parsed = parse_json_message(raw_text)
    score = score_case(normalized_case, parsed)
    result = {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "runner": "claude",
        "model": model,
        "reasoning_effort": effort,
        "skill_environment": skill_environment,
        "bundle_profile": bundle_profile,
        "bundle_chars": len(skill_bundle),
        "prompt_chars": len(prompt),
        "latency_ms": elapsed_ms,
        "usage": logs.get("usage"),
        "total_cost_usd": logs.get("total_cost_usd"),
        "expected": {
            "should_trigger": normalized_case["should_trigger"],
            "workflow": normalized_case["expected_workflow"],
            "mode": normalized_case["expected_mode"],
            "required_fields": normalized_case["required_fields"],
        },
        "actual": parsed,
        "score": score,
    }
    if include_logs:
        result["logs"] = logs
    return result


def select_cases(cases: list[dict], case_ids: list[str] | None, limit: int | None) -> list[dict]:
    selected = cases
    if case_ids:
        wanted = set(case_ids)
        selected = [case for case in selected if case["id"] in wanted]
    if limit is not None:
        selected = selected[:limit]
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run contract evals against thinking-clarity validation cases."
    )
    parser.add_argument(
        "--runner",
        choices=["codex", "openai", "claude"],
        default=os.getenv("THINKING_CLARITY_RUNNER", DEFAULT_RUNNER),
    )
    parser.add_argument("--cases-file", default=str(CASES_PATH))
    parser.add_argument("--model")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--codex-bin", default=os.getenv("CODEX_BIN", DEFAULT_CODEX_BIN))
    parser.add_argument("--claude-bin", default=os.getenv("CLAUDE_BIN", DEFAULT_CLAUDE_BIN))
    parser.add_argument("--timeout", type=int)
    parser.add_argument(
        "--skill-environment",
        default=os.getenv("THINKING_CLARITY_SKILL_ENVIRONMENT", "isolated"),
        choices=["isolated", "ambient"],
        help="Whether the local CLI runner should run with only this repo's isolated home config or also see your ambient local skill environment. Defaults to isolated.",
    )
    parser.add_argument(
        "--codex-reasoning-effort",
        default=os.getenv("CODEX_REASONING_EFFORT", DEFAULT_CODEX_REASONING_EFFORT),
        choices=["low", "medium", "high", "xhigh"],
        help="Reasoning effort for local Codex contract evals. Defaults to medium.",
    )
    parser.add_argument(
        "--bundle-profile",
        default="balanced",
        choices=sorted(VALID_BUNDLE_PROFILES),
        help="How much skill material to include in each contract eval prompt.",
    )
    parser.add_argument(
        "--claude-effort",
        default=os.getenv("CLAUDE_EFFORT", DEFAULT_CLAUDE_EFFORT),
        choices=["low", "medium", "high", "xhigh"],
        help="Effort level for Claude contract evals. xhigh maps to max.",
    )
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output")
    parser.add_argument(
        "--include-logs",
        action="store_true",
        help="Include CLI stdout/stderr excerpts in the saved report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any evaluated case fails.",
    )
    return parser.parse_args()


def write_output(path: str, results: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def build_error_result(
    case: dict,
    runner: str,
    model: str | None,
    bundle_profile: str,
    skill_environment: str | None,
    reasoning_effort: str | None,
    prompt_chars: int | None,
    bundle_chars: int | None,
    error: Exception,
) -> dict:
    normalized_case = normalize_expected_case(case)
    return {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "runner": runner,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "skill_environment": skill_environment,
        "bundle_profile": bundle_profile,
        "bundle_chars": bundle_chars,
        "prompt_chars": prompt_chars,
        "latency_ms": None,
        "usage": None,
        "expected": {
            "should_trigger": normalized_case["should_trigger"],
            "workflow": normalized_case["expected_workflow"],
            "mode": normalized_case["expected_mode"],
            "required_fields": normalized_case["required_fields"],
        },
        "actual": {
            "should_trigger": None,
            "workflow": [],
            "response_mode": "none",
            "boundary_reason": None,
            "sections": {},
            "final_answer": None,
        },
        "score": {
            "passed": False,
            "failed_checks": ["runner"],
            "missing_required_fields": [],
            "actual_workflow": "none",
            "actual_mode": "none",
        },
        "error": str(error),
    }


def print_summary(results: list[dict]) -> None:
    passed = sum(1 for item in results if item["score"]["passed"])
    failed = len(results) - passed
    print(f"Evaluated {len(results)} case(s)")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    for item in results:
        status = "PASS" if item["score"]["passed"] else "FAIL"
        print(f"[{status}] {item['case_id']}")
        print(
            "  expected:",
            item["expected"]["workflow"],
            "|",
            item["expected"]["mode"],
            "| trigger=" + str(item["expected"]["should_trigger"]),
        )
        print(
            "  actual:  ",
            item["score"]["actual_workflow"],
            "|",
            item["score"]["actual_mode"],
            "| trigger=" + str(item["actual"]["should_trigger"]),
        )
        if item["score"]["missing_required_fields"]:
            print(
                "  missing required fields:",
                ", ".join(item["score"]["missing_required_fields"]),
            )
        if item["score"]["failed_checks"]:
            print("  failed checks:", ", ".join(item["score"]["failed_checks"]))
        print(
            "  prompt_chars:",
            item.get("prompt_chars"),
            "| bundle_chars:",
            item.get("bundle_chars"),
            "| latency_ms:",
            item["latency_ms"],
        )
        if item.get("error"):
            print("  error:", item["error"])
        print()


def main() -> int:
    args = parse_args()
    cases_path = Path(args.cases_file)
    cases = load_cases(cases_path)
    selected_cases = select_cases(cases, args.case_ids, args.limit)
    if not selected_cases:
        print("No cases selected.", file=sys.stderr)
        return 2

    results = []
    if args.runner == "openai":
        openai_model = args.model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        timeout = args.timeout or 60
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY is required when --runner openai is used.", file=sys.stderr)
            return 2
        for case in selected_cases:
            try:
                results.append(
                    evaluate_case_openai(
                        case=case,
                        model=openai_model,
                        api_key=api_key,
                        base_url=args.base_url,
                        timeout=timeout,
                        bundle_profile=args.bundle_profile,
                    )
                )
            except Exception as exc:
                normalized_case = normalize_expected_case(case)
                skill_bundle = build_skill_bundle(normalized_case, bundle_profile=args.bundle_profile)
                prompt = build_eval_prompt(skill_bundle=skill_bundle, prompt=case["prompt"])
                results.append(
                    build_error_result(
                        case=case,
                        runner="openai",
                        model=openai_model,
                        bundle_profile=args.bundle_profile,
                        skill_environment=None,
                        reasoning_effort=None,
                        prompt_chars=len(prompt),
                        bundle_chars=len(skill_bundle),
                        error=exc,
                    )
                )
    elif args.runner == "codex":
        codex_model = args.model or os.getenv("CODEX_MODEL")
        timeout = args.timeout or DEFAULT_CODEX_TIMEOUT
        for case in selected_cases:
            try:
                results.append(
                    evaluate_case_codex(
                        case=case,
                        model=codex_model,
                        codex_bin=args.codex_bin,
                        timeout=timeout,
                        bundle_profile=args.bundle_profile,
                        reasoning_effort=args.codex_reasoning_effort,
                        skill_environment=args.skill_environment,
                        include_logs=args.include_logs,
                    )
                )
            except Exception as exc:
                normalized_case = normalize_expected_case(case)
                skill_bundle = build_skill_bundle(normalized_case, bundle_profile=args.bundle_profile)
                prompt = build_eval_prompt(skill_bundle=skill_bundle, prompt=case["prompt"])
                results.append(
                    build_error_result(
                        case=case,
                        runner="codex",
                        model=codex_model,
                        bundle_profile=args.bundle_profile,
                        skill_environment=args.skill_environment,
                        reasoning_effort=args.codex_reasoning_effort,
                        prompt_chars=len(prompt),
                        bundle_chars=len(skill_bundle),
                        error=exc,
                    )
                )
    else:
        claude_model = args.model or os.getenv("ANTHROPIC_MODEL")
        timeout = args.timeout or DEFAULT_CLAUDE_TIMEOUT
        for case in selected_cases:
            try:
                results.append(
                    evaluate_case_claude(
                        case=case,
                        model=claude_model,
                        claude_bin=args.claude_bin,
                        timeout=timeout,
                        bundle_profile=args.bundle_profile,
                        effort=args.claude_effort,
                        skill_environment=args.skill_environment,
                        include_logs=args.include_logs,
                    )
                )
            except Exception as exc:
                normalized_case = normalize_expected_case(case)
                skill_bundle = build_skill_bundle(normalized_case, bundle_profile=args.bundle_profile)
                prompt = build_eval_prompt(skill_bundle=skill_bundle, prompt=case["prompt"])
                results.append(
                    build_error_result(
                        case=case,
                        runner="claude",
                        model=claude_model,
                        bundle_profile=args.bundle_profile,
                        skill_environment=args.skill_environment,
                        reasoning_effort=args.claude_effort,
                        prompt_chars=len(prompt),
                        bundle_chars=len(skill_bundle),
                        error=exc,
                    )
                )

    summary = {
        "eval_type": "contract",
        "cases_file": str(cases_path),
        "runner": args.runner,
        "model": args.model
        or (
            os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
            if args.runner == "openai"
            else (
                os.getenv("CODEX_MODEL")
                if args.runner == "codex"
                else os.getenv("ANTHROPIC_MODEL")
            )
        ),
        "codex_reasoning_effort": (
            args.codex_reasoning_effort if args.runner == "codex" else None
        ),
        "claude_effort": args.claude_effort if args.runner == "claude" else None,
        "skill_environment": (
            args.skill_environment if args.runner in {"codex", "claude"} else None
        ),
        "bundle_profile": args.bundle_profile,
        "base_url": args.base_url if args.runner == "openai" else None,
        "total": len(results),
        "passed": sum(1 for item in results if item["score"]["passed"]),
        "failed": sum(1 for item in results if not item["score"]["passed"]),
        "results": results,
    }

    print_summary(results)
    if args.output:
        write_output(args.output, summary)
        print(f"Saved JSON report to {args.output}")

    if args.strict and summary["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
