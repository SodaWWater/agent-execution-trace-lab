from enum import Enum
from pathlib import Path
from ..providers.fake_model import FakeModel
from ..tools import ToolError, ToolRegistry
from ..trace.store import TraceStore


class State(str, Enum):
    RUNNING = "RUNNING"
    WAITING_TOOL = "WAITING_TOOL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentRuntime:
    def __init__(self, workspace: Path | str, trace_path: Path | str | None = None, max_iterations=8, model=None):
        self.workspace = Path(workspace)
        self.trace_path = Path(trace_path) if trace_path else self.workspace.parent.parent / "evidence" / "runtime" / "trace.json"
        self.max_iterations = max_iterations
        self.model = model or FakeModel()

    def run(self, task: str, failure_plan=None):
        trace = TraceStore(self.trace_path)
        registry = ToolRegistry(self.workspace, failure_plan)
        state = State.RUNNING
        observations = []
        trace.record(state.value, "task_started", input_summary=task)
        result = {"status": State.FAILED.value, "trace_path": str(self.trace_path)}
        for iteration in range(1, self.max_iterations + 1):
            context = {"task": task, "allowed_tools": ["list_files", "read_text", "write_report"], "observations": observations[-6:], "state": state.value}
            decision = self.model.decide(context)
            trace.record(state.value, "model_decision", input_summary={"iteration": iteration}, output_summary=decision)
            if decision.get("type") == "final":
                state = State.COMPLETED if decision.get("status") == "COMPLETED" else State.FAILED
                trace.record(state.value, "final_result", output_summary=decision.get("summary"))
                result = {"status": state.value, "summary": decision.get("summary"), "trace_path": str(trace.path)}
                break
            state = State.WAITING_TOOL
            name, params = decision.get("tool_name"), decision.get("input", {})
            trace.record(state.value, "tool_call_intent", tool_name=name, input_summary=params)
            try:
                output = registry.call(name, params)
                observations.append({"tool": name, "ok": True, "output": output})
                state = State.RUNNING
                trace.record(state.value, "tool_succeeded", tool_name=name, output_summary=output)
            except ToolError as exc:
                observations.append({"tool": name, "ok": False, "error": str(exc), "output": {}})
                state = State.RUNNING
                trace.record(state.value, "tool_failed", tool_name=name, error_type=type(exc).__name__, output_summary=str(exc))
                trace.record(state.value, "retry", tool_name=name, output_summary="retry allowed once")
        else:
            state = State.FAILED
            trace.record(state.value, "final_result", error_type="MaxIterationsExceeded", output_summary="maximum iterations exceeded")
            result = {"status": state.value, "summary": "maximum iterations exceeded", "trace_path": str(trace.path)}
        trace.save()
        return result
