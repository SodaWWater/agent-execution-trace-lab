# Agent Execution Trace Lab

这是一个基于开源 Agent 项目学习与二次开发的个人实验：用完全本地、确定性的采购异常订单核查任务，观察状态机、受限工具调用、故障恢复和可回放 Execution Trace。上游源码不在本仓库中，项目仅保留学习边界说明；Fake Model 只用于编排与安全测试，不代表模型能力评测。

## 场景与实现

输入自然语言核查目标后，运行时依次列出样本、读取订单和规则，并写入审批摘要。一次可控的读取失败会被记录为结构化错误并重试一次。

```text
任务 -> Runtime 上下文 -> Fake Model -> 调用意图 Trace -> 受限工具 -> 观察 Trace -> 摘要
```

工具边界：`list_files` 只能列出 `fixtures/workspace`；`read_text` 只能读取其中的 UTF-8 文本；`write_report` 只能写入 `fixtures/workspace/reports/`。绝对路径、`..`、未知字段和越界写入都会被拒绝。详见 `docs/architecture.md` 与 `docs/threat-model.md`。

## 运行

```powershell
python -m unittest discover -s tests -v
python scripts/run_demo.py --mode normal
python scripts/run_demo.py --mode failure
```

演示会打印 Trace 和报告路径；示例结果保存在 `evidence/examples/`，运行时文件在 `evidence/runtime/`（被 git 忽略）。Trace 事件包含任务开始、模型决策、工具调用意图、成功/失败、重试和最终结果。

样本均为自建数据，不包含真实业务信息，也不访问网络、Docker 或外部模型服务。
