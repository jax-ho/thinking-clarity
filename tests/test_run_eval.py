import importlib.util
import unittest
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "run_eval.py"
    spec = importlib.util.spec_from_file_location("run_eval", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RunEvalTests(unittest.TestCase):
    def test_extract_structured_output_text_from_response(self):
        module = load_module()
        response = {
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": '{"should_trigger": true}'}
                    ],
                }
            ]
        }
        self.assertEqual(module.extract_output_text(response), '{"should_trigger": true}')

    def test_score_trigger_case_detects_full_pass(self):
        module = load_module()
        expected = {
            "id": "case-1",
            "should_trigger": True,
            "expected_workflow": "clarify>decide",
            "expected_mode": "Structured Analysis",
            "required_fields": ["real_goal", "recommendation", "next_move"],
        }
        actual = {
            "should_trigger": True,
            "workflow": ["clarify", "decide"],
            "response_mode": "Structured Analysis",
            "sections": {
                "real_goal": "Clarify the actual decision.",
                "recommendation": "Choose the smaller path first.",
                "next_move": "Test the smaller path this week.",
            },
            "final_answer": "Choose the smaller path first and test it this week.",
        }
        result = module.score_case(expected, actual)
        self.assertTrue(result["passed"])
        self.assertEqual(result["failed_checks"], [])

    def test_score_trigger_case_detects_missing_required_field(self):
        module = load_module()
        expected = {
            "id": "case-2",
            "should_trigger": True,
            "expected_workflow": "deconstruct",
            "expected_mode": "Structured Analysis",
            "required_fields": ["recommendation", "next_move"],
        }
        actual = {
            "should_trigger": True,
            "workflow": ["deconstruct"],
            "response_mode": "Structured Analysis",
            "sections": {
                "recommendation": "",
                "next_move": "Inspect the boundary causing duplication first.",
            },
            "final_answer": "Inspect the boundary causing duplication first.",
        }
        result = module.score_case(expected, actual)
        self.assertFalse(result["passed"])
        self.assertIn("required_fields", result["failed_checks"])

    def test_score_non_trigger_case_detects_false_positive(self):
        module = load_module()
        expected = {
            "id": "case-3",
            "should_trigger": False,
            "expected_workflow": "none",
            "expected_mode": "none",
            "required_fields": [],
        }
        actual = {
            "should_trigger": True,
            "workflow": ["clarify"],
            "response_mode": "Quick Reframe",
            "sections": {},
            "final_answer": "You should rename the helper.",
        }
        result = module.score_case(expected, actual)
        self.assertFalse(result["passed"])
        self.assertIn("should_trigger", result["failed_checks"])

    def test_build_skill_bundle_is_smaller_in_balanced_mode_than_full(self):
        module = load_module()
        case = {
            "id": "case-3b",
            "should_trigger": True,
            "case_type": "clean_trigger",
            "expected_workflow": "Simplify -> Decide",
            "expected_mode": "Structured Analysis",
        }
        balanced = module.build_skill_bundle(case, bundle_profile="balanced")
        full = module.build_skill_bundle(case, bundle_profile="full")
        self.assertLess(len(balanced), len(full))

    def test_score_trigger_case_accepts_alternative_workflow(self):
        module = load_module()
        expected = {
            "id": "case-4",
            "should_trigger": True,
            "expected_workflow": "simplify>decide",
            "acceptable_workflows": [
                "simplify>decide",
                "clarify>deconstruct>simplify>decide",
            ],
            "expected_mode": "Structured Analysis",
            "required_fields": ["real_goal", "recommendation", "next_move"],
        }
        actual = {
            "should_trigger": True,
            "workflow": ["clarify", "deconstruct", "simplify", "decide"],
            "response_mode": "Structured Analysis",
            "sections": {
                "real_goal": "Validate the workflow before framework cost.",
                "recommendation": "Script one path first.",
                "next_move": "Implement one narrow scripted flow.",
            },
            "final_answer": "Script one narrow flow first.",
        }
        result = module.score_case(expected, actual)
        self.assertTrue(result["passed"])

    def test_score_trigger_case_accepts_alternative_mode(self):
        module = load_module()
        expected = {
            "id": "case-5",
            "should_trigger": True,
            "expected_workflow": "deconstruct>decide",
            "expected_mode": "Structured Analysis",
            "acceptable_modes": ["Structured Analysis", "Pressure Test"],
            "required_fields": ["real_goal", "recommendation", "next_move"],
        }
        actual = {
            "should_trigger": True,
            "workflow": ["deconstruct", "decide"],
            "response_mode": "Pressure Test",
            "sections": {
                "real_goal": "Decide whether this refactor should happen now.",
                "recommendation": "Do the smallest refactor tied to delivery risk.",
                "next_move": "List the concrete blockers on the next feature set.",
            },
            "final_answer": "Do the smallest refactor tied to concrete blockers.",
        }
        result = module.score_case(expected, actual)
        self.assertTrue(result["passed"])

    def test_build_codex_command_sets_noninteractive_options(self):
        module = load_module()
        command = module.build_codex_command(
            codex_bin="codex",
            model=None,
            output_path=Path("/tmp/out.json"),
            reasoning_effort="medium",
            schema_path=Path("/tmp/schema.json"),
        )
        self.assertEqual(command[0:2], ["codex", "exec"])
        self.assertIn("--output-schema", command)
        self.assertIn("--output-last-message", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("read-only", command)
        self.assertIn('model_reasoning_effort="medium"', command)
        self.assertNotIn("--model", command)

    def test_parse_json_message_accepts_fenced_json(self):
        module = load_module()
        parsed = module.parse_json_message(
            "```json\n{\"should_trigger\": false, \"workflow\": [], \"response_mode\": \"none\", \"boundary_reason\": \"mechanical\", \"sections\": {}, \"final_answer\": null}\n```"
        )
        self.assertFalse(parsed["should_trigger"])

    def test_structured_output_schema_only_requires_case_fields(self):
        module = load_module()
        schema = module.structured_output_schema(["real_goal", "next_move"])
        self.assertEqual(
            schema["properties"]["sections"]["required"],
            ["real_goal", "next_move"],
        )
        self.assertEqual(
            set(schema["properties"]["sections"]["properties"]),
            {"real_goal", "next_move"},
        )

    def test_build_claude_command_uses_print_json_and_effort(self):
        module = load_module()
        command = module.build_claude_command(
            claude_bin="claude",
            model="sonnet",
            prompt="Return JSON",
            effort="xhigh",
            schema={"type": "object"},
        )
        self.assertEqual(command[0:2], ["claude", "-p"])
        self.assertIn("--output-format", command)
        self.assertIn("json", command)
        self.assertIn("--json-schema", command)
        self.assertIn("--effort", command)
        self.assertIn("max", command)
        self.assertIn("--model", command)

    def test_extract_claude_result_prefers_structured_output(self):
        module = load_module()
        response = {
            "result": '{"wrong":"shape"}',
            "structured_output": {"answer": "OK"},
        }
        self.assertEqual(
            module.extract_claude_result(response, schema={"type": "object"}),
            '{"answer": "OK"}',
        )


if __name__ == "__main__":
    unittest.main()
