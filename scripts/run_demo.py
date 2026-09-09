import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_trace_lab.runtime import AgentRuntime

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["normal", "failure"], required=True)
args = parser.parse_args()
workspace = ROOT / "fixtures" / "workspace"
trace_path = ROOT / "evidence" / "runtime" / f"trace-{args.mode}.json"
result = AgentRuntime(workspace, trace_path).run("核查采购异常订单并生成审批摘要", {"read_text_once": True} if args.mode == "failure" else None)
print(f"trace_path: {trace_path}")
print(f"report_path: {workspace / 'reports' / 'order-review.md'}")
print(f"final_status: {result['status']}")
