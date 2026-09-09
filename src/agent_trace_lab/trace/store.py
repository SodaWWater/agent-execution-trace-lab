import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class TraceStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.trace_id = str(uuid.uuid4())
        self.events = []

    def record(self, state, event_type, tool_name=None, input_summary=None,
               output_summary=None, error_type=None):
        event = {
            "trace_id": self.trace_id,
            "event_id": len(self.events) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state,
            "event_type": event_type,
            "tool_name": tool_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "error_type": error_type,
        }
        self.events.append(event)
        return event

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"trace_id": self.trace_id, "events": self.events}, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.path
