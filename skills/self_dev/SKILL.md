---
name: self_dev
description: Self-modification tools for reading/writing source code, running tests, and git commits
tools:
  - read_source
  - write_source
  - run_tests
  - git_commit
---

# Self-Modification Skill

Allows the agent to inspect and modify its own codebase.
All writes require human approval unless SELF_DEV_APPROVAL_REQUIRED is set to false.
