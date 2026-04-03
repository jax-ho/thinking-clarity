import importlib.util
import unittest
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "trigger_eval.py"
    spec = importlib.util.spec_from_file_location("trigger_eval", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TriggerEvalTests(unittest.TestCase):
    def test_build_claude_command_uses_json_print_mode(self):
        module = load_module()
        command = module.build_claude_command(
            claude_bin="claude",
            prompt="Reply with JSON",
            reasoning_effort="xhigh",
            model="sonnet",
            schema={"type": "object"},
        )
        self.assertEqual(command[0:2], ["claude", "-p"])
        self.assertIn("--json-schema", command)
        self.assertIn("--effort", command)
        self.assertIn("max", command)
        self.assertIn("--model", command)

    def test_extract_claude_result_uses_result_text_without_schema(self):
        module = load_module()
        response = {"result": "OK"}
        self.assertEqual(module.extract_claude_result(response, schema=None), "OK")

    def test_score_positive_case_requires_trigger_and_effect(self):
        module = load_module()
        case = {
            "id": "trigger-1",
            "should_trigger": True,
            "expected_effects": ["gives a recommendation"],
            "disallowed_effects": [],
        }
        judgment = {
            "looks_like_skill_triggered": True,
            "effect_passed": True,
            "missing_effects": [],
            "disallowed_effects_seen": [],
            "summary": "Good answer.",
        }
        result = module.score_case(case, "Recommend the smaller path first.", judgment)
        self.assertTrue(result["passed"])

    def test_score_negative_case_fails_when_skill_style_appears(self):
        module = load_module()
        case = {
            "id": "trigger-2",
            "should_trigger": False,
            "expected_effects": ["answers directly"],
            "disallowed_effects": ["reframes the question"],
        }
        judgment = {
            "looks_like_skill_triggered": True,
            "effect_passed": False,
            "missing_effects": ["answers directly"],
            "disallowed_effects_seen": ["reframes the question"],
            "summary": "Over-analysis.",
        }
        result = module.score_case(case, "Let's step back and reframe this.", judgment)
        self.assertFalse(result["passed"])
        self.assertIn("trigger", result["failed_checks"])
        self.assertIn("effect", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
