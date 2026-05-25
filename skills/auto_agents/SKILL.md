# Auto Agents

Automatically create and manage sub-agents for complex tasks.

## Description
Analyzes incoming tasks and spawns specialized sub-agents to handle different aspects in parallel.

## Usage
```python
from core.auto_agent_factory import AutoAgentFactory
from core.agent_store import AgentStore

store = AgentStore()
factory = AutoAgentFactory(store)
result = factory.spawn_for_task("Research AI trends and write a summary")
```

## Behavior
1. LLM analyzes the task to identify sub-tasks
2. Creates temporary agent configs for each sub-task
3. Runs agents in parallel via ThreadPoolExecutor
4. Synthesizes results into a unified response
5. Cleans up temporary agents
