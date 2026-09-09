class FakeModel:
    """Deterministic policy used to exercise orchestration, not model quality."""
    def decide(self, context):
        observations = context.get("observations", [])
        if not any(o.get("tool") == "list_files" and o.get("ok") for o in observations):
            return {"type": "tool", "tool_name": "list_files", "input": {"relative_dir": "."}}
        if not any(o.get("tool") == "read_text" and o.get("ok") for o in observations):
            return {"type": "tool", "tool_name": "read_text", "input": {"relative_path": "orders.json"}}
        if not any(o.get("tool") == "write_report" and o.get("ok") for o in observations):
            text = next((o.get("output", {}).get("text", "") for o in observations if o.get("tool") == "read_text" and o.get("ok")), "")
            return {"type": "tool", "tool_name": "write_report", "input": {"relative_path": "reports/order-review.md", "content": "# 采购异常订单核查摘要\n\n" + text}}
        return {"type": "final", "status": "COMPLETED", "summary": "审批摘要已写入 reports/order-review.md"}
