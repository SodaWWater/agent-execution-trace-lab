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

    def test_report_summarizes_flagged_order(self):
        result, _ = self.run_runtime()
        self.assertEqual(result["status"], State.COMPLETED.value)
        report = (ROOT / "fixtures" / "workspace" / "reports" / "order-review.md").read_text(encoding="utf-8")
        for expected in ("PO-1001", "华北供应商", "12800", "金额超过 10000 元", "待审批", "需要人工复核"):
            self.assertIn(expected, report)

    def test_trace_reads_rules_before_writing_report(self):
        result, path = self.run_runtime()
        self.assertEqual(result["status"], State.COMPLETED.value)
        events = json.loads(path.read_text(encoding="utf-8"))["events"]
        tool_successes = [
            e["tool_name"] for e in events if e["event_type"] == "tool_succeeded"
        ]
        self.assertEqual(tool_successes[:4], ["list_files", "read_text", "read_text", "write_report"])
        read_intents = [
            e["input_summary"].get("relative_path")
            for e in events
            if e["event_type"] == "tool_call_intent" and e["tool_name"] == "read_text"
        ]
        self.assertIn("rules.md", read_intents)

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
        result, path = self.run_runtime({"read_text_once": True})
        events = json.loads(path.read_text())["events"]
        intent_counts = {}
        execution_counts = {}
        for index, event in enumerate(events):
            tool = event.get("tool_name")
            if event["event_type"] == "tool_call_intent":
                intent_counts[tool] = intent_counts.get(tool, 0) + 1
            elif event["event_type"] in {"tool_succeeded", "tool_failed"}:
                execution_counts[tool] = execution_counts.get(tool, 0) + 1
                self.assertGreaterEqual(
                    intent_counts.get(tool, 0), execution_counts[tool],
                    f"execution for {tool} occurred before its intent",
                )


if __name__ == "__main__":
    unittest.main()
