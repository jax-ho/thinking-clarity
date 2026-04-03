#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from codex_isolation import claude_home_environment, codex_home_environment

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "scripts" / "trigger_cases.json"
DEFAULT_CODEX_TIMEOUT = 180
DEFAULT_CLAUDE_TIMEOUT = 300
DEFAULT_CODEX_BIN = "codex"
DEFAULT_CLAUDE_BIN = "claude"
DEFAULT_RUNNER = "claude"
DEFAULT_ANSWER_REASONING_EFFORT = "medium"
DEFAULT_JUDGE_REASONING_EFFORT = "low"
CLAUDE_TRIGGER_SYSTEM_PROMPT = (
    "Treat the user prompt as a standalone prompt. "
    "Do not inspect the workspace, repository, or files. "
    "Do not ask to inspect code or gather local context unless the prompt itself provides it."
)
CLAUDE_JUDGE_SYSTEM_PROMPT = (
    "Grade only the prompt and answer provided. "
    "Do not inspect the workspace, repository, or files."
)


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def summarize_process_output(text: str, limit: int = 1200) -> str:
    if not text:
        return ""
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:400] + "\n...\n" + stripped[-700:]


def normalize_claude_effort(effort: str) -> str:
    return {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "xhigh": "max",
    }[effort]


def build_codex_command(
    codex_bin: str,
    output_path: Path,
    reasoning_effort: str,
    model: str | None = None,
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
    prompt: str,
    reasoning_effort: str,
    model: str | None = None,
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
        normalize_claude_effort(reasoning_effort),
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


def run_codex(
    prompt: str,
    codex_bin: str,
    timeout: int,
    reasoning_effort: str,
    skill_environment: str,
    install_skill: bool,
    model: str | None = None,
    schema: dict | None = None,
) -> tuple[str, dict]:
    with codex_home_environment(skill_environment, install_skill=install_skill) as env:
        with tempfile.TemporaryDirectory(prefix="thinking-clarity-trigger-") as tmpdir:
            output_path = Path(tmpdir) / "last_message.txt"
            schema_path: Path | None = None
            if schema is not None:
                schema_path = Path(tmpdir) / "schema.json"
                schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

            cmd = build_codex_command(
                codex_bin=codex_bin,
                output_path=output_path,
                reasoning_effort=reasoning_effort,
                model=model,
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
                "installed_skill": install_skill,
            }


def extract_claude_result(response: dict, schema: dict | None) -> str:
    if schema is not None and isinstance(response.get("structured_output"), dict):
        return json.dumps(response["structured_output"], ensure_ascii=False)
    result = response.get("result")
    if isinstance(result, str):
        return result
    raise ValueError("Could not find Claude result text in CLI response")


def run_claude(
    prompt: str,
    claude_bin: str,
    timeout: int,
    reasoning_effort: str,
    skill_environment: str,
    install_skill: bool,
    model: str | None = None,
    schema: dict | None = None,
    system_prompt: str | None = None,
) -> tuple[str, dict]:
    with claude_home_environment(skill_environment, install_skill=install_skill) as env:
        cmd = build_claude_command(
            claude_bin=claude_bin,
            prompt=prompt,
            reasoning_effort=reasoning_effort,
            model=model,
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
            "installed_skill": install_skill,
            "usage": parsed_stdout.get("usage"),
            "total_cost_usd": parsed_stdout.get("total_cost_usd"),
        }


def build_answer_prompt(prompt: str) -> str:
    return prompt


def judge_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "looks_like_skill_triggered": {"type": "boolean"},
            "effect_passed": {"type": "boolean"},
            "missing_effects": {
                "type": "array",
                "items": {"type": "string"},
            },
            "disallowed_effects_seen": {
                "type": "array",
                "items": {"type": "string"},
            },
            "summary": {"type": "string"},
        },
        "required": [
            "looks_like_skill_triggered",
            "effect_passed",
            "missing_effects",
            "disallowed_effects_seen",
            "summary",
        ],
    }


def build_judge_prompt(case: dict, answer_text: str) -> str:
    expected = "\n".join(f"- {item}" for item in case["expected_effects"])
    disallowed = "\n".join(f"- {item}" for item in case["disallowed_effects"])
    return f"""You are grading whether an assistant answer shows the intended effect of the thinking-clarity skill.

The skill is supposed to do this when it applies:
- clarify the real problem
- expose the relevant facts or constraints
- reduce false complexity
- end with a recommendation or next move

The skill is not supposed to take over requests that are mainly debugging, brainstorming, factual lookup, direct conventional answers, low-risk choices, or pure execution.

Case metadata:
- should_trigger: {str(case["should_trigger"]).lower()}
- category: {case["category"]}
- case_type: {case["case_type"]}
- failure_risk: {case["failure_risk"]}

User prompt:
{case["prompt"]}

Expected effects:
{expected}

Disallowed effects:
{disallowed}

Assistant answer:
{answer_text}

Judging rules:
- looks_like_skill_triggered = whether the answer behaves like thinking-clarity rather than a direct conventional answer
- effect_passed = whether the answer satisfies the expected effects and avoids the disallowed effects for this case
- missing_effects should list concrete expected effects that were not met
- disallowed_effects_seen should list concrete disallowed effects that appeared
"""


def score_case(case: dict, answer_text: str, judgment: dict) -> dict:
    failed_checks: list[str] = []

    if case["should_trigger"]:
        if not judgment["looks_like_skill_triggered"]:
            failed_checks.append("trigger")
    else:
        if judgment["looks_like_skill_triggered"]:
            failed_checks.append("trigger")

    if not judgment["effect_passed"]:
        failed_checks.append("effect")

    if not answer_text.strip():
        failed_checks.append("answer")

    return {
        "passed": not failed_checks,
        "failed_checks": failed_checks,
    }


def evaluate_case(
    case: dict,
    runner: str,
    codex_bin: str,
    claude_bin: str,
    timeout: int,
    answer_reasoning_effort: str,
    judge_reasoning_effort: str,
    skill_environment: str,
    answer_model: str | None,
    judge_model: str | None,
    include_logs: bool,
) -> dict:
    started = time.time()
    answer_runner = run_codex if runner == "codex" else run_claude
    answer_kwargs = {
        "prompt": build_answer_prompt(case["prompt"]),
        "timeout": timeout,
        "reasoning_effort": answer_reasoning_effort,
        "skill_environment": skill_environment,
        "install_skill": (skill_environment == "isolated"),
        "model": answer_model,
        "schema": None,
        "system_prompt": None if runner == "codex" else CLAUDE_TRIGGER_SYSTEM_PROMPT,
    }
    if runner == "codex":
        answer_kwargs["codex_bin"] = codex_bin
    else:
        answer_kwargs["claude_bin"] = claude_bin
    answer_text, answer_logs = answer_runner(**answer_kwargs)
    answer_elapsed_ms = int((time.time() - started) * 1000)

    judge_started = time.time()
    judge_runner = run_codex if runner == "codex" else run_claude
    judge_kwargs = {
        "prompt": build_judge_prompt(case, answer_text),
        "timeout": timeout,
        "reasoning_effort": judge_reasoning_effort,
        "skill_environment": "isolated",
        "install_skill": False,
        "model": judge_model,
        "schema": judge_schema(),
        "system_prompt": None if runner == "codex" else CLAUDE_JUDGE_SYSTEM_PROMPT,
    }
    if runner == "codex":
        judge_kwargs["codex_bin"] = codex_bin
    else:
        judge_kwargs["claude_bin"] = claude_bin
    judge_text, judge_logs = judge_runner(**judge_kwargs)
    judge_elapsed_ms = int((time.time() - judge_started) * 1000)
    judgment = parse_json_message(judge_text)
    score = score_case(case, answer_text, judgment)

    result = {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "runner": runner,
        "answer_reasoning_effort": answer_reasoning_effort,
        "judge_reasoning_effort": judge_reasoning_effort,
        "skill_environment": skill_environment,
        "latency_ms": answer_elapsed_ms + judge_elapsed_ms,
        "answer_latency_ms": answer_elapsed_ms,
        "judge_latency_ms": judge_elapsed_ms,
        "expected": {
            "should_trigger": case["should_trigger"],
            "expected_effects": case["expected_effects"],
            "disallowed_effects": case["disallowed_effects"],
        },
        "actual": {
            "answer_text": answer_text,
            "judgment": judgment,
        },
        "score": score,
    }
    if include_logs:
        result["logs"] = {
            "answer": answer_logs,
            "judge": judge_logs,
        }
    return result


def select_cases(cases: list[dict], case_ids: list[str] | None, limit: int | None) -> list[dict]:
    selected = cases
    if case_ids:
        wanted = set(case_ids)
        selected = [case for case in selected if case["id"] in wanted]
    if limit is not None:
        selected = selected[:limit]
    return selected


def write_output(path: str, payload: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def build_error_result(
    case: dict,
    answer_reasoning_effort: str,
    judge_reasoning_effort: str,
    skill_environment: str,
    error: Exception,
) -> dict:
    return {
        "case_id": case["id"],
        "prompt": case["prompt"],
        "answer_reasoning_effort": answer_reasoning_effort,
        "judge_reasoning_effort": judge_reasoning_effort,
        "skill_environment": skill_environment,
        "latency_ms": None,
        "answer_latency_ms": None,
        "judge_latency_ms": None,
        "expected": {
            "should_trigger": case["should_trigger"],
            "expected_effects": case["expected_effects"],
            "disallowed_effects": case["disallowed_effects"],
        },
        "actual": {
            "answer_text": "",
            "judgment": {
                "looks_like_skill_triggered": False,
                "effect_passed": False,
                "missing_effects": [],
                "disallowed_effects_seen": [],
                "summary": f"runner error: {error}",
            },
        },
        "score": {
            "passed": False,
            "failed_checks": ["runner"],
        },
        "error": str(error),
    }


def print_summary(results: list[dict]) -> None:
    passed = sum(1 for item in results if item["score"]["passed"])
    failed = len(results) - passed
    print(f"Evaluated {len(results)} trigger case(s)")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    for item in results:
        status = "PASS" if item["score"]["passed"] else "FAIL"
        print(f"[{status}] {item['case_id']}")
        print(
            "  expected trigger:",
            item["expected"]["should_trigger"],
            "| judged trigger:",
            item["actual"]["judgment"]["looks_like_skill_triggered"],
        )
        if item["actual"]["judgment"]["missing_effects"]:
            print(
                "  missing effects:",
                ", ".join(item["actual"]["judgment"]["missing_effects"]),
            )
        if item["actual"]["judgment"]["disallowed_effects_seen"]:
            print(
                "  disallowed seen:",
                ", ".join(item["actual"]["judgment"]["disallowed_effects_seen"]),
            )
        if item["score"]["failed_checks"]:
            print("  failed checks:", ", ".join(item["score"]["failed_checks"]))
        print(
            "  answer_ms:",
            item["answer_latency_ms"],
            "| judge_ms:",
            item["judge_latency_ms"],
            "| total_ms:",
            item["latency_ms"],
        )
        if item.get("error"):
            print("  error:", item["error"])
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run real trigger evals for thinking-clarity using a local CLI environment."
    )
    parser.add_argument("--cases-file", default=str(CASES_PATH))
    parser.add_argument(
        "--runner",
        choices=["codex", "claude"],
        default=os.getenv("THINKING_CLARITY_TRIGGER_RUNNER", DEFAULT_RUNNER),
    )
    parser.add_argument("--codex-bin", default=os.getenv("CODEX_BIN", DEFAULT_CODEX_BIN))
    parser.add_argument("--claude-bin", default=os.getenv("CLAUDE_BIN", DEFAULT_CLAUDE_BIN))
    parser.add_argument("--timeout", type=int)
    parser.add_argument(
        "--skill-environment",
        default=os.getenv("THINKING_CLARITY_SKILL_ENVIRONMENT", "isolated"),
        choices=["isolated", "ambient"],
        help="Use isolated to test with only this skill installed. Use ambient to let the local CLI see your normal local skill environment.",
    )
    parser.add_argument(
        "--answer-reasoning-effort",
        default=os.getenv("CODEX_REASONING_EFFORT", DEFAULT_ANSWER_REASONING_EFFORT),
        choices=["low", "medium", "high", "xhigh"],
    )
    parser.add_argument(
        "--judge-reasoning-effort",
        default=os.getenv("THINKING_CLARITY_JUDGE_REASONING_EFFORT", DEFAULT_JUDGE_REASONING_EFFORT),
        choices=["low", "medium", "high", "xhigh"],
    )
    parser.add_argument("--answer-model")
    parser.add_argument("--judge-model")
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output")
    parser.add_argument("--include-logs", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases_path = Path(args.cases_file)
    cases = load_cases(cases_path)
    selected_cases = select_cases(cases, args.case_ids, args.limit)
    if not selected_cases:
        print("No cases selected.", file=sys.stderr)
        return 2

    results = []
    timeout = args.timeout or (
        DEFAULT_CODEX_TIMEOUT if args.runner == "codex" else DEFAULT_CLAUDE_TIMEOUT
    )
    for case in selected_cases:
        try:
            results.append(
                evaluate_case(
                    case=case,
                    runner=args.runner,
                    codex_bin=args.codex_bin,
                    claude_bin=args.claude_bin,
                    timeout=timeout,
                    answer_reasoning_effort=args.answer_reasoning_effort,
                    judge_reasoning_effort=args.judge_reasoning_effort,
                    skill_environment=args.skill_environment,
                    answer_model=args.answer_model,
                    judge_model=args.judge_model,
                    include_logs=args.include_logs,
                )
            )
        except Exception as exc:
            results.append(
                build_error_result(
                    case=case,
                    answer_reasoning_effort=args.answer_reasoning_effort,
                    judge_reasoning_effort=args.judge_reasoning_effort,
                    skill_environment=args.skill_environment,
                    error=exc,
                )
            )

    summary = {
        "eval_type": "trigger",
        "cases_file": str(cases_path),
        "total": len(results),
        "passed": sum(1 for item in results if item["score"]["passed"]),
        "failed": sum(1 for item in results if not item["score"]["passed"]),
        "runner": args.runner,
        "answer_reasoning_effort": args.answer_reasoning_effort,
        "judge_reasoning_effort": args.judge_reasoning_effort,
        "skill_environment": args.skill_environment,
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
