# My Agent — Project Vision

## Overview

My Agent is a modular AI agent system with a web-based management interface, inspired by AutoGPT, OpenSwarm, and Hermes Desktop. It provides a Universal Assistant that auto-selects skills based on user requests, alongside specialized agents for specific domains.

## Core Value Proposition

1. **Universal Assistant** — One chat interface that auto-selects from 11 skills and 14 tools
2. **Agent Ecosystem** — 7 specialized agents (researcher, developer, marketer, data_analyst, slides, docs, universal)
3. **Auto-Agent Factory** — LLM-based dynamic agent spawning with parallel sub-agent execution
4. **Production-Ready** — SQLite persistence, retry logic, async concurrency, safety guardrails

## Target Users

- Solo developers who need an AI assistant with persistent memory
- Small teams wanting a self-hosted alternative to ChatGPT with custom skills
- Power users who need specialized agents (deep research, data analysis, presentations)

## Technology Stack

- **Backend:** Python 3.11+, FastAPI, LiteLLM (OpenRouter)
- **Frontend:** Vanilla HTML/JS, SSE streaming, dark theme
- **Persistence:** SQLite with WAL mode, FTS5 full-text search
- **Concurrency:** ThreadPoolExecutor + asyncio.to_thread()
- **Models:** DeepSeek V4 Flash (free) via OpenRouter, with fallback

## Architecture Philosophy

- **Modularity:** Skills and tools are self-registering via YAML frontmatter and Python modules
- **Extensibility:** New skills can be added without touching core code
- **Resilience:** Jittered exponential backoff, fallback models, error sanitization
- **Observability:** Structured logging with session context, rotating files, secret redaction

## Current Status (v1.0)

All 5 production-critical issues have been fixed:
1. Async concurrency via `asyncio.to_thread()` and `asyncio.gather()`
2. SQLite WAL persistence with FTS5 search
3. Retry logic with `jittered_backoff()` and error classification
4. Safety guardrails: iteration budget, loop detection, tool error sanitization
5. Centralized logging: `agent.log`, `errors.log`, `web.log` with `RedactingFormatter`

## Next Milestone (v1.1)

See `ROADMAP.md` for detailed phase planning.
