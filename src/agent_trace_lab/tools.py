import json
from pathlib import Path


class ToolError(Exception):
    pass


class ToolRegistry:
    """Three allow-listed tools over a fixture workspace."""
    def __init__(self, workspace: Path | str, failure_plan=None):
        self.workspace = Path(workspace).resolve()
        self.failure_plan = failure_plan or {}
        self._failures = set()

    def _validate(self, params, required):
        if not isinstance(params, dict) or set(params) != {required}:
            raise ToolError(f"invalid fields for tool (expected exactly {required})")
        value = params[required]
        if not isinstance(value, str) or not value:
            raise ToolError("path must be a non-empty string")
        p = Path(value)
        if p.is_absolute() or ".." in p.parts:
            raise ToolError("path must be relative and cannot contain ..")
        return value

    def _inside(self, relative, *, reports_only=False):
        target = (self.workspace / relative).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError:
            raise ToolError("path escapes fixture workspace")
        if reports_only:
            reports = (self.workspace / "reports").resolve()
            try:
                target.relative_to(reports)
            except ValueError:
                raise ToolError("reports must be under workspace/reports")
        return target

    def call(self, name, params):
        if name == "list_files":
            return self.list_files(params)
        if name == "read_text":
            return self.read_text(params)
        if name == "write_report":
            return self.write_report(params)
        raise ToolError(f"unknown tool: {name}")

    def list_files(self, params):
        rel = self._validate(params, "relative_dir")
        base = self._inside(rel)
        if not base.is_dir():
            raise ToolError("directory does not exist")
        files = sorted(str(p.relative_to(self.workspace)).replace("\\", "/") for p in base.rglob("*") if p.is_file())
        return {"files": files}

    def read_text(self, params):
        rel = self._validate(params, "relative_path")
        if self.failure_plan.get("read_text_once") and "read_text_once" not in self._failures:
            self._failures.add("read_text_once")
            raise ToolError("injected read_text failure")
        target = self._inside(rel)
        if not target.is_file():
            raise ToolError("file does not exist")
        try:
            return {"text": target.read_text(encoding="utf-8")}
        except UnicodeDecodeError as exc:
            raise ToolError("file is not UTF-8 text") from exc

    def write_report(self, params):
        if not isinstance(params, dict) or set(params) != {"relative_path", "content"}:
            raise ToolError("write_report expects relative_path and content only")
        rel = self._validate({"relative_path": params["relative_path"]}, "relative_path")
        if not isinstance(params["content"], str):
            raise ToolError("content must be a string")
        target = self._inside(rel, reports_only=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(params["content"], encoding="utf-8")
        return {"path": str(target.relative_to(self.workspace)).replace("\\", "/"), "bytes": target.stat().st_size}
