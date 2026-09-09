import json


class FakeModel:
    """Deterministic policy used to exercise orchestration, not model quality."""

    def decide(self, context):
        observations = context.get("observations", [])
        if not any(o.get("tool") == "list_files" and o.get("ok") for o in observations):
            return {"type": "tool", "tool_name": "list_files", "input": {"relative_dir": "."}}

        successful_reads = [
            o.get("output", {}).get("text", "")
            for o in observations
            if o.get("tool") == "read_text" and o.get("ok")
        ]
        orders_text = successful_reads[0] if successful_reads else None
        if orders_text is None:
            return {"type": "tool", "tool_name": "read_text", "input": {"relative_path": "orders.json"}}

        rules_text = successful_reads[1] if len(successful_reads) > 1 else None
        if rules_text is None:
            return {"type": "tool", "tool_name": "read_text", "input": {"relative_path": "rules.md"}}

        if not any(o.get("tool") == "write_report" and o.get("ok") for o in observations):
            content = self._render_summary(orders_text, rules_text)
            return {
                "type": "tool",
                "tool_name": "write_report",
                "input": {"relative_path": "reports/order-review.md", "content": content},
            }
        return {"type": "final", "status": "COMPLETED", "summary": "审批摘要已写入 reports/order-review.md"}

    @staticmethod
    def _render_summary(orders_text, rules_text):
        data = json.loads(orders_text)
        orders = data.get("orders", [])
        flagged = [order for order in orders if order.get("status") == "pending" and order.get("amount", 0) > 10000]
        lines = ["# 采购异常订单核查摘要", "", "## 审批结论", ""]
        if not flagged:
            lines.append("未发现需要人工复核的待审批订单。")
        else:
            lines.append("以下订单金额超过 10000 元且状态为待审批，需要人工复核：")
            lines.append("")
            for order in flagged:
                reason = order.get("flag") or "金额超过 10000 元"
                lines.extend(
                    [
                        f"- 订单编号：{order.get('id', '')}",
                        f"- 供应商：{order.get('supplier', '')}",
                        f"- 金额：{order.get('amount', '')}",
                        "- 状态：待审批",
                        f"- 异常原因：{reason}；金额超过 10000 元，需要人工复核。",
                        "",
                    ]
                )
        lines.extend(["## 规则依据", "", rules_text.strip(), ""])
        return "\n".join(lines)
