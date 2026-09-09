# Threat model

The trust boundary is the fixture workspace. Tools reject absolute paths, traversal, unknown fields, non-text files, and writes outside `workspace/reports/`. No shell, network, subprocess, credentials, plugin protocol, or arbitrary filesystem API is exposed. The failure plan is local test input and can inject only one read failure.
