---
name: code_execution
description: "Write, test, and execute code. Run scripts, validate logic, debug issues."
version: 1.0
tools:
  - execute_code
  - file_read
  - file_write
triggers:
  - execute
  - run code
  - test
  - debug
  - запусти код
---

# Code Execution Skill

## Instructions
When asked to execute or test code:
1. Use file_read if code is in a file
2. Use execute_code to run it
3. Analyze output and errors
4. Fix issues and re-run if needed
5. Use file_write to save results
