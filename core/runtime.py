"""Async-native AgentRuntime."""
import json
import os
import re
import sys
import logging
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from core.iteration_budget import IterationBudget, BudgetExhaustedError
from core.kimi_provider import extract_message_content
from core.skill_cache import filter_skills_by_query

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

console = Console(force_terminal=True)
logger = logging.getLogger(__name__)


_TOOL_ERROR_MAX_LEN = 2000
_TOOL_ERROR_ROLE_TAG_RE = re.compile(
    r"</?(?:tool_call|function_call|result|response|output|input|system|assistant|user)>",
    re.IGNORECASE,
)
_TOOL_ERROR_FENCE_RE = re.compile(r"```(?:json|xml|html|markdown)?\s*", re.MULTILINE)
_TOOL_ERROR_CDATA_RE = re.compile(r"<!\[CDATA\[.*?\]\]>", re.DOTALL)


def _parse_tool_calls_from_text(content: str):
    """Fallback parser for models that emit tool calls as text/XML instead of structured tool_calls."""
    if not content or not content.strip():
        return []
    
    # Pattern 1: XML-like longcat tags (e.g. <longcat_arg_key>query</longcat_arg_key>)
    # Detect if content contains longcat tags
    if "<longcat_arg_key>" in content or "<tool>" in content or "<function>" in content:
        # Try to extract function name (first word before tags)
        lines = content.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("```"):
                continue
            # Find first word (function name)
            parts = line.split("<", 1)
            if len(parts) < 2:
                continue
            func_name = parts[0].strip()
            if not func_name:
                continue
            
            # Extract args from <longcat_arg_key>key</longcat_arg_key> <longcat_arg_value>value</longcat_arg_value>
            args = {}
            key_pattern = re.findall(r"<longcat_arg_key>([^<]+)</longcat_arg_key>\s*<longcat_arg_value>([^<]+)</longcat_arg_value>", line)
            for k, v in key_pattern:
                # Try to parse numbers
                try:
                    if v.isdigit():
                        v = int(v)
                    elif "." in v and v.replace(".", "", 1).isdigit():
                        v = float(v)
                except (ValueError, AttributeError):
                    pass
                args[k] = v
            
            # Build fake tool_call object compatible with existing code
            class FakeToolCall:
                def __init__(self, name, arguments, idx):
                    self.id = f"call_fallback_{idx}"
                    self.function = FakeFunction(name, arguments)
            
            class FakeFunction:
                def __init__(self, name, arguments):
                    self.name = name
                    self.arguments = json.dumps(arguments) if arguments else "{}"
            
            return [FakeToolCall(func_name, args, 0)]
    
    # Pattern 2: JSON tool call in text (e.g. {"name": "web_search", "arguments": {"query": "..."}})
    json_match = re.search(r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}', content)
    if json_match:
        func_name = json_match.group(1)
        args_str = json_match.group(2)
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            args = {}
        
        class FakeToolCall:
            def __init__(self, name, arguments, idx):
                self.id = f"call_fallback_{idx}"
                self.function = FakeFunction(name, arguments)
        
        class FakeFunction:
            def __init__(self, name, arguments):
                self.name = name
                self.arguments = json.dumps(arguments) if arguments else "{}"
        
        return [FakeToolCall(func_name, args, 0)]
    
    return []


def _sanitize_tool_error(error_msg: str) -> str:
    """Strip structural framing tokens from tool errors before showing to model."""
    if not error_msg:
        return "[TOOL_ERROR] "
    sanitized = _TOOL_ERROR_ROLE_TAG_RE.sub("", error_msg)
    sanitized = _TOOL_ERROR_FENCE_RE.sub("", sanitized)
    sanitized = _TOOL_ERROR_CDATA_RE.sub("", sanitized)
    if len(sanitized) > _TOOL_ERROR_MAX_LEN:
        sanitized = sanitized[:_TOOL_ERROR_MAX_LEN - 3] + "..."
    return f"[TOOL_ERROR] {sanitized}"


class AgentRuntime:
    def __init__(self, llm, role, skills, memory, tool_names=None, integrations=None, events=None, compressor=None, plugins=None):
        self.llm = llm
        self.role = role
        self.skills = skills
        self.memory = memory
        self.tool_names = tool_names or []
        self.integrations = integrations or {}
        self.events = events
        self.compressor = compressor
        self.plugins = plugins

    async def _execute_tools_parallel(self, tool_calls, session, recent_tool_calls, budget):
        """Execute multiple independent tools in parallel."""
        import asyncio
        LOOP_DETECTION_WINDOW = 5
        LOOP_REPEAT_THRESHOLD = 3
        tasks = []
        tool_calls_raw = []
        results = []

        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}

            # --- Loop detection ---
            call_signature = (tool_name, json.dumps(args, sort_keys=True))
            recent_tool_calls.append(call_signature)
            if len(recent_tool_calls) > LOOP_DETECTION_WINDOW:
                recent_tool_calls.pop(0)

            if len(recent_tool_calls) >= LOOP_REPEAT_THRESHOLD:
                last_n = recent_tool_calls[-LOOP_REPEAT_THRESHOLD:]
                if all(c == last_n[0] for c in last_n):
                    loop_msg = (
                        f"Loop detected: tool '{tool_name}' called {LOOP_REPEAT_THRESHOLD} "
                        f"times with identical arguments. Stopping to prevent infinite loop."
                    )
                    logger.warning(loop_msg)
                    console.print(f"[red]{loop_msg}[/red]")
                    session.add_assistant_message(
                        f"I detected a potential infinite loop with tool '{tool_name}'. "
                        f"The same arguments were repeated {LOOP_REPEAT_THRESHOLD} times. "
                        f"Please review your request or try a different approach."
                    )
                    return None, "loop_detected"

            if self.events:
                self.events.emit("on_tool_call", tool=tool_name, args=args)
            if self.plugins:
                self.plugins.emit("on_tool_call", tool=tool_name, args=args)

            console.print(f"[yellow]Tool:[/yellow] {tool_name}({args})")

            # Create async task for tool execution
            async def _run_tool(name, arguments):
                try:
                    result = self.skills.execute_tool(name, **arguments)
                    return name, arguments, result, None
                except Exception as e:
                    return name, arguments, None, e

            tasks.append(_run_tool(tool_name, args))

            if hasattr(tc, "id"):
                tool_calls_raw.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        # Execute all tools in parallel
        executed = await asyncio.gather(*tasks)

        for tool_name, args, result, error in executed:
            if error:
                result_str = f"Error executing {tool_name}: {error}"
                logger.exception(result_str)
            else:
                result_str = str(result)

            sanitized_result = _sanitize_tool_error(result_str)
            display_result = sanitized_result[:200]
            if len(sanitized_result) > 200:
                display_result += "..."
            console.print(f"[green]Result ({tool_name}):[/green] {display_result}")

            results.append(sanitized_result)

        return tool_calls_raw, results

    async def run(self, user_input, session_id=None):
        """Async-native agent execution loop with parallel tool execution."""
        session = await self.memory.ensure_session(session_id or "default")
        session.add_user_message(user_input)

        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + session.messages

        if self.events:
            await self.events.emit_async("on_message", message=user_input, session=session)
        if self.plugins:
            self.plugins.emit("on_message", message=user_input, session=session)

        console.print(Panel(f"[bold blue]Задача:[/bold blue] {user_input}", title="Agent"))

        budget = IterationBudget(max_iterations=90, warning_thresholds=[10, 5, 1])
        recent_tool_calls = []

        max_turns = 20
        turn = 0

        while turn < max_turns:
            turn += 1

            try:
                budget.consume()
            except BudgetExhaustedError as e:
                logger.error(str(e))
                console.print(f"[red]{e}[/red]")
                return (
                    f"I reached the maximum number of tool calls ({budget.max_iterations}) "
                    f"for this request. Please break your request into smaller sub-tasks."
                )

            if self.compressor and self.compressor.needs_compression(messages):
                console.print("[dim]Сжатие контекста...[/dim]")
                messages = await self.compressor.compress_async(messages)

            # Get all available tools
            all_tools = self.skills.get_schemas(self.tool_names) if self.tool_names else self.skills.get_schemas()

            # Pre-filter skills based on user query to save tokens
            if all_tools and turn == 1:  # Only on first turn when we have the original query
                tool_names = [t.get("function", {}).get("name", "") for t in all_tools]
                filtered_names = filter_skills_by_query(user_input, tool_names)
                tools = [t for t in all_tools if t.get("function", {}).get("name", "") in filtered_names]
                console.print(f"[dim]Skills pre-filtered: {len(tools)}/{len(all_tools)} relevant[/dim]")
            else:
                tools = all_tools

            console.print("[dim]Вызов LLM...[/dim]")
            response = await self.llm.chat(messages, tools=tools if tools else None)

            # Handle error responses gracefully
            if hasattr(response, "content") and response.content and response.content.startswith("I encountered an error"):
                session.add_assistant_message(response.content)
                if self.memory.enabled:
                    await self.memory.persist_session(session)
                return response.content

            # Parse tool calls: structured first, then fallback to text parsing
            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls and hasattr(response, "content") and response.content:
                parsed = _parse_tool_calls_from_text(response.content)
                if parsed:
                    tool_calls = parsed
                    logger.info("Parsed %d tool calls from text fallback", len(parsed))
            
            if tool_calls:
                # Execute tools in parallel
                tool_calls_raw, results = await self._execute_tools_parallel(
                    tool_calls, session, recent_tool_calls, budget
                )

                if results == "loop_detected":
                    if self.memory.enabled:
                        await self.memory.persist_session(session)
                    return session.messages[-1]["content"]

                # Add all tool results to messages
                for i, tc in enumerate(tool_calls):
                    if i < len(results):
                        tc_id = getattr(tc, "id", f"call_fallback_{i}")
                        session.add_tool_result(tc_id, results[i])

                if tool_calls_raw:
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls_raw,
                    })
                continue

            final_response = extract_message_content(response)
            session.add_assistant_message(final_response)

            if self.events:
                self.events.emit("on_response", response=final_response)
            if self.plugins:
                self.plugins.emit("on_response", response=final_response)

            console.print(Panel(Markdown(final_response), title="Ответ агента"))

            if self.memory.enabled:
                await self.memory.persist_session(session)

            return final_response

        console.print("[red]Max turns reached[/red]")
        return session.messages[-1]["content"] if session.messages else ""

    def _build_system_prompt(self):
        parts = [self.role]
        skills_context = self.skills.get_context()
        if skills_context:
            parts.append(skills_context)
        return "\n\n".join(parts)
