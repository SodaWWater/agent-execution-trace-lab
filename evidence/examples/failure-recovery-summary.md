# Failure recovery example

`python scripts/run_demo.py --mode failure` injects one local `read_text` failure. The trace records `tool_failed`, `retry`, a successful second read, and ends in `COMPLETED`.
