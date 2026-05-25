"""Async-native parallel agent execution."""
import asyncio
from core.builder import AgentBuilder


async def run_parallel_agents_async(user_input, agent_configs):
    """Asynchronous parallel agent execution using asyncio.gather.

    Each agent runs natively async — no thread wrapping needed.
    Up to 8 agents run in parallel via semaphore.
    """
    semaphore = asyncio.Semaphore(8)

    async def _run_one(config):
        async with semaphore:
            builder = (AgentBuilder()
                .set_model(config.get("model", {}))
                .set_role(config.get("role", ""))
                .set_skills(config.get("skills", []))
                .set_tools(config.get("tools", []))
                .set_memory(config.get("memory", {"enabled": False}))
                .enable_events(False)
                .enable_compression(True)
                .enable_plugins(False)
            )
            agent = builder.build()
            return await agent.run(user_input)

    tasks = []
    for config in agent_configs:
        task = asyncio.create_task(_run_one(config))
        task._agent_id = config["id"]
        tasks.append(task)

    results = {}
    for task in tasks:
        agent_id = getattr(task, "_agent_id", "unknown")
        try:
            results[agent_id] = await task
        except Exception as e:
            results[agent_id] = f"Error: {str(e)}"

    return results


def run_parallel_agents(user_input, agent_configs):
    """Synchronous parallel agent execution (backward compatibility).

    Delegates to async version via asyncio.run().
    """
    return asyncio.run(run_parallel_agents_async(user_input, agent_configs))
