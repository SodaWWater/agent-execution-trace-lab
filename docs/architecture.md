# Architecture

`AgentRuntime` coordinates a deterministic `FakeModel`, an allow-listed `ToolRegistry`, and `TraceStore`. Each loop assembles bounded context, records a decision, records tool intent, executes one local tool, then records the observation. State transitions are `RUNNING -> WAITING_TOOL -> RUNNING`, ending in `COMPLETED` or `FAILED`.

```text
task -> runtime/context -> fake model -> intent trace -> local tool -> observation trace
                                      \-> retry (one injected failure)
```
