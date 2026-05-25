def spawn_sub_agents(task_description, agent_store, llm_config=None):
    from core.auto_agent_factory import AutoAgentFactory
    factory = AutoAgentFactory(agent_store, llm_config)
    return factory.spawn_for_task(task_description)


def analyze_task(task_description, agent_store, llm_config=None):
    from core.auto_agent_factory import AutoAgentFactory
    factory = AutoAgentFactory(agent_store, llm_config)
    return factory._analyze_task(task_description)


def list_active_agents(agent_store):
    agents = agent_store.list_agents()
    return [a for a in agents if not a.get("_temp", False)]


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="spawn_sub_agents",
        description="Spawn parallel sub-agents to handle different aspects of a complex task simultaneously",
        parameters={"type": "object", "properties": {
            "task_description": {"type": "string"},
        }},
        execute_fn=lambda task_description="":
            spawn_sub_agents(task_description, __import__('core.agent_store', fromlist=['AgentStore']).AgentStore()),
    )
    registry.register(
        name="analyze_task",
        description="Analyze a task description and identify sub-tasks that can be parallelized",
        parameters={"type": "object", "properties": {
            "task_description": {"type": "string"},
        }},
        execute_fn=lambda task_description="":
            analyze_task(task_description, __import__('core.agent_store', fromlist=['AgentStore']).AgentStore()),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["spawn_sub_agents", "analyze_task"]:
        registry.unregister(name)
