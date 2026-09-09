"""Compatibility helper documenting the deterministic failure switch."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent_trace_lab.tools import ToolRegistry

registry = ToolRegistry(Path(__file__).resolve().parents[1] / "fixtures" / "workspace", {"read_text_once": True})
try:
    registry.read_text({"relative_path": "orders.json"})
except Exception as exc:
    print(f"injected failure: {exc}")
