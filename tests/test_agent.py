import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent_trace_lab.runtime import AgentRuntime, State
from agent_trace_lab.tools import ToolError, ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


class LoopModel:
    def decide(self, context):
        return {"type": "tool", "tool_name": "list_files", "input": {"relative_dir": "."}}


class AgentTests(unittest.TestCase):
    def run_runtime(self, failure_plan=None, **kwargs):
        path = Path(tempfile.mkdtemp()) / "trace.json"
        return AgentRuntime(ROOT / "fixtures" / "workspace", path, **kwargs).run("核查订单", failure_plan), path

    def test_normal_completed(self):
        result, _ = self.run_runtime()
        self.assertEqual(result["status"], State.COMPLETED.value)

    def test_failure_retries(self):
        result, path = self.run_runtime({"read_text_once": True})
        self.assertEqual(result["status"], "COMPLETED")
        events = json.loads(path.read_text())["events"]
        self.assertTrue(any(e["event_type"] == "retry" for e in events))

    def test_illegal_paths_rejected(self):
        tools = ToolRegistry(ROOT / "fixtures" / "workspace")
        for params in ({"relative_path": "../secret"}, {"relative_path": str(Path.cwd() / "x")}):
            with self.assertRaises(ToolError):
                tools.read_text(params)
        with self.assertRaises(ToolError):
            tools.write_report({"relative_path": "notes.md", "content": "x"})

    def test_max_iterations_failed(self):
        result, _ = self.run_runtime(max_iterations=2, model=LoopModel())
        self.assertEqual(result["status"], "FAILED")

    def test_intent_before_execution(self):
        result, path = self.run_runtime()
        events = json.loads(path.read_text())["events"]
        intents = [e["event_id"] for e in events if e["event_type"] == "tool_call_intent"]
        successes = [e["event_id"] for e in events if e["event_type"] == "tool_succeeded"]
        self.assertTrue(intents and successes)
        self.assertLess(intents[0], successes[0])


if __name__ == "__main__":
    unittest.main()
