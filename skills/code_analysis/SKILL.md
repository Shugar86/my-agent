---
name: code_analysis
description: "Analyze code, find issues, suggest improvements, review code quality."
version: 1.0
tools:
  - file_read
  - execute_code
triggers:
  - analyze
  - review
  - code quality
  - проанализируй код
  - ревью
---

# Code Analysis Skill

## Instructions
When asked to analyze code:
1. Use file_read to get the code
2. Analyze for: bugs, style issues, performance, security
3. Provide structured report with severity levels
4. Suggest specific fixes
