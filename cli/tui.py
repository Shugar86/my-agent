#!/usr/bin/env python3
"""My Agent CLI TUI — Rich-based terminal interface."""

# Load .env before any other imports
from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.style import Style
from rich import box

# Project imports
from core.config import load_agent_config, resolve_env_vars
from core.builder import AgentBuilder
from core.agent_store import AgentStore
from core.state_db import StateDB
from core.llm_gateway import LLMGateway

# Auto UTF-8
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')


class AgentTUI:
    """Rich-based Terminal UI for My Agent."""

    def __init__(
        self,
        agent_id: str = "universal",
        model_profile: str = "fast",
        session_id: Optional[str] = None,
    ):
        self.console = Console(
            color_system="auto",
            width=120,
            soft_wrap=True,
        )
        self.agent_id = agent_id
        self.model_profile = model_profile
        self.store = AgentStore()
        self.state_db = StateDB("data/cli_sessions.db")

        # Agent config
        self.agent_config = self.store.get_agent(agent_id) or {}
        if not self.agent_config:
            self.console.print(f"[bold red]Агент '{agent_id}' не найден[/]")
            sys.exit(1)

        # Model config
        self.config = load_agent_config()
        self.model_config = self._resolve_model_config(model_profile)
        self.model_name = self.model_config.get("primary", "unknown").split("/")[-1]

        # Session
        self.session_id = session_id or f"cli_{int(time.time() * 1000)}"
        self.session_title = None
        self.language = self._detect_language()
        self.messages: List[Dict[str, Any]] = []

        # Agent instance
        self.agent = None
        self._init_agent()

        # Stats
        self.total_latency = 0.0
        self.message_count = 0
        self.tool_calls_count = 0

        # UI strings
        self._i18n = self._load_i18n()

    def _resolve_model_config(self, profile: str) -> dict:
        """Resolve model profile to full config."""
        profiles = {
            "fast": "openai/gpt-5.4-nano",
            "balanced": "openrouter/owl-alpha",
            "smart": "anthropic/claude-sonnet-4",
            "local": "ollama/llama3",
        }
        model_raw = self.config.get("model", {})
        if isinstance(model_raw, str):
            model_raw = {"primary": model_raw}

        if profile in profiles:
            model_raw = dict(model_raw)
            model_raw["primary"] = profiles[profile]

        return resolve_env_vars(model_raw)

    def _init_agent(self):
        """Build agent from config."""
        builder = AgentBuilder()
        builder.set_model(self.model_config)
        builder.set_role(self.agent_config.get("role", ""))
        builder.set_skills(self.agent_config.get("skills", []))
        builder.set_tools(self.agent_config.get("tools", []))
        builder.set_memory(self.agent_config.get("memory", {"enabled": True}))
        self.agent = builder.build()

    def _detect_language(self) -> str:
        """Auto-detect language from system or env."""
        lang = os.environ.get("LANG", "")
        if "ru" in lang.lower():
            return "ru"
        return "ru"  # Default to Russian for this user base

    def _load_i18n(self) -> dict:
        """Localized UI strings."""
        return {
            "ru": {
                "welcome_title": "My Agent — Интерактивный режим",
                "agent_label": "Агент",
                "model_label": "Модель",
                "skills_label": "Навыков",
                "tools_label": "Инструментов",
                "commands_hint": "Команды",
                "thinking": "думает",
                "you": "Вы",
                "agent": "Агент",
                "latency": "задержка",
                "tokens": "токенов",
                "tools_used": "инструментов",
                "new_session": "Новая сессия создана",
                "history_title": "История сессий",
                "no_history": "История пуста",
                "session_loaded": "Сессия загружена",
                "session_not_found": "Сессия не найдена",
                "search_results": "Результаты поиска",
                "no_results": "Ничего не найдено",
                "title_set": "Название установлено",
                "forked": "Сессия форкнута",
                "model_changed": "Модель изменена",
                "agent_changed": "Агент изменён",
                "cleared": "История очищена",
                "goodbye": "До свидания! Сессия сохранена.",
                "help_title": "Доступные команды",
                "unknown_cmd": "Неизвестная команда",
                "suggestions": "Подсказка",
                "press_enter": "Нажмите Enter",
                "status_title": "Статус системы",
            },
            "en": {
                "welcome_title": "My Agent — Interactive Mode",
                "agent_label": "Agent",
                "model_label": "Model",
                "skills_label": "Skills",
                "tools_label": "Tools",
                "commands_hint": "Commands",
                "thinking": "thinking",
                "you": "You",
                "agent": "Agent",
                "latency": "latency",
                "tokens": "tokens",
                "tools_used": "tools used",
                "new_session": "New session created",
                "history_title": "Session History",
                "no_history": "No history",
                "session_loaded": "Session loaded",
                "session_not_found": "Session not found",
                "search_results": "Search Results",
                "no_results": "No results",
                "title_set": "Title set",
                "forked": "Session forked",
                "model_changed": "Model changed",
                "agent_changed": "Agent changed",
                "cleared": "History cleared",
                "goodbye": "Goodbye! Session saved.",
                "help_title": "Available Commands",
                "unknown_cmd": "Unknown command",
                "suggestions": "Hint",
                "press_enter": "Press Enter",
                "status_title": "System Status",
            },
        }.get(self.language, "ru")

    def _t(self, key: str) -> str:
        """Get translated string."""
        return self._i18n.get(key, key)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_welcome(self):
        """Print welcome screen."""
        # ASCII art
        logo = Text.assemble(
            ("╔══════════════════════════════════════════════════════════════╗\n", "bold cyan"),
            ("║  ", "bold cyan"),
            ("[ My Agent ]", "bold white on cyan"),
            ("  AI-powered automation system  v2026.05                      ║\n", "bold cyan"),
            ("╠══════════════════════════════════════════════════════════════╣\n", "bold cyan"),
            ("║  ", "bold cyan"),
            ("🤖", ""),
            (f"  {self._t('agent_label')}: ", "dim"),
            (f"{self.agent_config.get('name', self.agent_id)}", "bold green"),
            (f"  ({self.agent_id})", "dim"),
            ("                                        ║\n", "bold cyan"),
            ("║  ", "bold cyan"),
            ("⚡", ""),
            (f"  {self._t('model_label')}: ", "dim"),
            (f"{self.model_name}", "bold yellow"),
            (f"  [{self.model_profile}]", "dim"),
            ("                                 ║\n", "bold cyan"),
            ("║  ", "bold cyan"),
            ("🛠️ ", ""),
            (f"  {self._t('skills_label')}: ", "dim"),
            (f"{len(self.agent_config.get('skills', []))}", "bold blue"),
            (f"  |  {self._t('tools_label')}: ", "dim"),
            (f"{len(self.agent_config.get('tools', []))}", "bold blue"),
            ("                                  ║\n", "bold cyan"),
            ("╚══════════════════════════════════════════════════════════════╝", "bold cyan"),
        )

        self.console.print()
        self.console.print(logo)

        # Commands hint
        self.console.print(
            f"\n[dim]{self._t('commands_hint')}: "
            f"[bold]/help[/], [bold]/new[/], [bold]/history[/], "
            f"[bold]/model[/], [bold]/agent[/], [bold]/clear[/], [bold]/quit[/][/dim]\n"
        )

        # Separator (status bar will add Rule before prompt)
        self.console.print()

    def render_user_message(self, text: str):
        """Render user message."""
        user_text = Text.from_markup(f"[bold blue]{self._t('you')}:[/] {text}")
        self.console.print(user_text)
        self.console.print()

    def render_assistant_message(self, text: str, latency: float = 0):
        """Render assistant message with markdown and code blocks."""
        # Detect code blocks and render with syntax highlighting
        parts = self._split_code_blocks(text)

        for part in parts:
            if part["type"] == "markdown":
                self.console.print(Markdown(part["content"]))
            elif part["type"] == "code":
                syntax = Syntax(
                    part["content"],
                    part.get("lang", "text"),
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True,
                )
                self.console.print(Panel(syntax, border_style="dim green", padding=(0, 1)))

        # Stats footer
        if latency > 0:
            stats = Text.assemble(
                ("  ⏱ ", "dim"),
                (f"{latency:.1f}s", "dim yellow"),
                (f" | {self.model_name}", "dim"),
            )
            self.console.print(stats)

        self.console.print()

    def _split_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Split text into markdown and code blocks."""
        parts = []
        pattern = r'```(\w*)\n(.*?)```'
        last_end = 0

        for match in re.finditer(pattern, text, re.DOTALL):
            # Markdown before code
            if match.start() > last_end:
                parts.append({
                    "type": "markdown",
                    "content": text[last_end:match.start()].strip(),
                })
            # Code block
            lang = match.group(1).strip() or "text"
            code = match.group(2).strip()
            parts.append({"type": "code", "content": code, "lang": lang})
            last_end = match.end()

        # Remaining markdown
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                parts.append({"type": "markdown", "content": remaining})

        if not parts:
            parts.append({"type": "markdown", "content": text})

        return parts

    def render_thinking(self, tools: Optional[List[str]] = None):
        """Render thinking spinner with optional tool preview."""
        tool_str = ""
        if tools:
            tool_str = f" [{', '.join(tools)}]"

        spinner_text = f"[dim yellow]⏳ {self._t('thinking')}...{tool_str}[/]"
        self.console.print(spinner_text)

    def render_tool_call(self, tool_name: str, args: dict):
        """Render tool call info."""
        table = Table(
            show_header=False,
            box=box.ROUNDED,
            border_style="dim yellow",
            width=80,
            padding=(0, 1),
        )
        table.add_column(style="bold yellow", width=12)
        table.add_column(style="dim")
        table.add_row("🛠️ Tool", tool_name)

        for k, v in args.items():
            v_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
            table.add_row(f"  {k}", v_str)

        self.console.print(table)
        self.console.print()

    def render_status_bar(self):
        """Render bottom status bar."""
        status = Table.grid(padding=(0, 2))
        status.add_column(style="bold cyan")
        status.add_column(style="dim")
        status.add_column(style="bold green")
        status.add_column(style="dim")

        status.add_row(
            "🤖", self.agent_id,
            "⚡", self.model_name,
        )

        avg_latency = self.total_latency / max(self.message_count, 1)
        status.add_row(
            "⏱", f"{avg_latency:.1f}s avg",
            "💬", f"{self.message_count} msg",
        )

        self.console.print(Rule(style="dim"))
        self.console.print(status)
        self.console.print()

    def render_error(self, error: str):
        """Render error message."""
        self.console.print(Panel(
            f"[bold red]❌ {error}[/]",
            border_style="red",
            title="Error",
            title_align="left",
        ))
        self.console.print()

    def render_success(self, message: str):
        """Render success message."""
        self.console.print(f"[bold green]✅ {message}[/]")
        self.console.print()

    # ------------------------------------------------------------------
    # Session Management
    # ------------------------------------------------------------------

    def _create_session(self):
        """Create new session in StateDB."""
        self.state_db.create_session(
            session_id=self.session_id,
            source="cli",
            model=self.model_name,
            model_config=self.model_config,
            user_id="cli_user",
        )

    def _save_message(self, role: str, content: str, tool_name: str = None):
        """Save message to StateDB. Creates session if not exists."""
        # Ensure session exists
        existing = self.state_db.get_session(self.session_id)
        if not existing:
            self._create_session()
        self.state_db.add_message(
            session_id=self.session_id,
            role=role,
            content=content,
            tool_name=tool_name,
        )
        if role in ("user", "assistant"):
            self.state_db.update_message_count(self.session_id)

    def _load_session(self, session_id: str) -> bool:
        """Load existing session messages."""
        session = self.state_db.get_session(session_id)
        if not session:
            return False

        self.session_id = session_id
        self.session_title = session.get("title")

        rows = self.state_db.get_messages(session_id)
        self.messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row["tool_call_id"]:
                msg["tool_call_id"] = row["tool_call_id"]
            self.messages.append(msg)

        # Update stats
        self.message_count = len([m for m in self.messages if m["role"] in ("user", "assistant")])

        return True

    def _list_sessions(self, limit: int = 20) -> List[Dict]:
        """List recent sessions."""
        return self.state_db.list_sessions(limit=limit)

    def _fork_session(self) -> str:
        """Fork current session."""
        new_id = f"cli_{int(time.time() * 1000)}"
        self.state_db.create_session(
            session_id=new_id,
            source="cli",
            model=self.model_name,
            model_config=self.model_config,
            parent_session_id=self.session_id,
        )

        # Copy messages from DB (not self.messages, which may be stale)
        rows = self.state_db.get_messages(self.session_id)
        for row in rows:
            self.state_db.add_message(
                session_id=new_id,
                role=row["role"],
                content=row.get("content", ""),
            )

        return new_id

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def handle_command(self, cmd: str) -> bool:
        """Handle slash command. Returns True if should continue."""
        parts = cmd.strip().split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if action in ("/quit", "/exit", "/q"):
            self._save_message("system", "Session ended by user")
            self.state_db.end_session(self.session_id, "user_quit")
            self.render_success(self._t("goodbye"))
            return False

        if action == "/help":
            self._show_help()
            return True

        if action == "/clear":
            self.messages = []
            self.console.clear()
            self.render_welcome()
            self.render_success(self._t("cleared"))
            return True

        if action == "/new":
            self._save_message("system", "Session closed for new session")
            self.state_db.end_session(self.session_id, "new_session")
            self.session_id = f"cli_{int(time.time() * 1000)}"
            self.messages = []
            self.session_title = None
            self._create_session()
            self.render_success(self._t("new_session"))
            return True

        if action == "/history":
            self._show_history()
            return True

        if action == "/resume":
            if not arg:
                self.render_error("Usage: /resume <session_id>")
                return True
            if self._load_session(arg):
                self.render_success(f"{self._t('session_loaded')}: {arg}")
                # Show loaded messages
                for msg in self.messages:
                    if msg["role"] == "user":
                        self.render_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        self.render_assistant_message(msg["content"])
            else:
                self.render_error(self._t("session_not_found"))
            return True

        if action == "/title":
            if not arg:
                self.render_error("Usage: /title <name>")
                return True
            self.session_title = arg
            self.state_db.set_session_title(self.session_id, arg)
            self.render_success(f"{self._t('title_set')}: {arg}")
            return True

        if action == "/search":
            if not arg:
                self.render_error("Usage: /search <query>")
                return True
            self._do_search(arg)
            return True

        if action == "/fork":
            new_id = self._fork_session()
            self.render_success(f"{self._t('forked')}: {new_id}")
            return True

        if action == "/model":
            if not arg:
                self._show_model_info()
                return True
            if arg in ("fast", "balanced", "smart", "local"):
                self.model_profile = arg
                self.model_config = self._resolve_model_config(arg)
                self.model_name = self.model_config.get("primary", "unknown").split("/")[-1]
                self._init_agent()
                self.render_success(f"{self._t('model_changed')}: {self.model_name}")
            else:
                self.render_error(f"Unknown model profile: {arg}. Use: fast, balanced, smart, local")
            return True

        if action == "/agent":
            if not arg:
                self._show_agent_info()
                return True
            config = self.store.get_agent(arg)
            if config:
                self.agent_id = arg
                self.agent_config = config
                self._init_agent()
                self.render_success(f"{self._t('agent_changed')}: {config.get('name', arg)}")
            else:
                self.render_error(f"Agent '{arg}' not found")
            return True

        if action == "/status":
            self._show_status()
            return True

        self.render_error(f"{self._t('unknown_cmd')}: {action}")
        return True

    def _show_help(self):
        """Show help table."""
        table = Table(
            title=self._t("help_title"),
            box=box.ROUNDED,
            border_style="cyan",
            header_style="bold cyan",
        )
        table.add_column("Команда", style="bold yellow", width=14)
        table.add_column("Описание", style="")
        table.add_column("Пример", style="dim")

        commands = [
            ("/help", "Показать эту справку", ""),
            ("/new", "Создать новую сессию", ""),
            ("/history", "Список сессий", ""),
            ("/resume <id>", "Загрузить сессию", "/resume cli_123"),
            ("/title <name>", "Назвать сессию", "/title проект_А"),
            ("/search <q>", "Поиск по истории", "/search docker"),
            ("/fork", "Форкнуть сессию", ""),
            ("/model [name]", "Сменить модель", "/model smart"),
            ("/agent [id]", "Сменить агента", "/agent developer"),
            ("/status", "Статус системы", ""),
            ("/clear", "Очистить экран", ""),
            ("/quit", "Выйти", ""),
        ]
        for cmd, desc, example in commands:
            table.add_row(cmd, desc, example)

        self.console.print(table)
        self.console.print()

    def _show_history(self):
        """Show session history table."""
        sessions = self._list_sessions()
        if not sessions:
            self.render_success(self._t("no_history"))
            return

        table = Table(
            title=self._t("history_title"),
            box=box.ROUNDED,
            border_style="cyan",
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim", width=20)
        table.add_column("Название", style="bold")
        table.add_column("Сообщений", style="", width=10)
        table.add_column("Модель", style="dim", width=15)
        table.add_column("Дата", style="dim", width=16)

        for s in sessions:
            started = datetime.fromtimestamp(s["started_at"]).strftime("%d.%m %H:%M")
            table.add_row(
                s["id"][:18],
                s.get("title", "—") or "—",
                str(s.get("message_count", 0)),
                (s.get("model") or "—")[:14],
                started,
            )

        self.console.print(table)
        self.console.print()

    def _do_search(self, query: str):
        """Search messages via FTS5."""
        results = self.state_db.search_messages(query)
        if not results:
            self.render_success(self._t("no_results"))
            return

        table = Table(
            title=f"{self._t('search_results')}: '{query}'",
            box=box.ROUNDED,
            border_style="cyan",
        )
        table.add_column("Сессия", style="dim", width=18)
        table.add_column("Название", style="bold", width=20)
        table.add_column("Сообщение", style="")
        table.add_column("Дата", style="dim", width=16)

        for r in results[:20]:
            ts = datetime.fromtimestamp(r["timestamp"]).strftime("%d.%m %H:%M")
            content = (r["content"] or "")[:80] + "..." if len(r.get("content", "")) > 80 else (r["content"] or "")
            table.add_row(
                r["session_id"][:16],
                (r.get("title") or "—")[:18],
                content,
                ts,
            )

        self.console.print(table)
        self.console.print()

    def _show_model_info(self):
        """Show current model config."""
        table = Table(title="Model Configuration", box=box.ROUNDED)
        table.add_column("Параметр", style="bold")
        table.add_column("Значение", style="")
        table.add_row("Profile", self.model_profile)
        table.add_row("Primary", self.model_config.get("primary", "—"))
        table.add_row("Fallback", self.model_config.get("fallback", "—"))
        table.add_row("Max tokens", str(self.model_config.get("params", {}).get("max_tokens", "—")))
        table.add_row("Temperature", str(self.model_config.get("params", {}).get("temperature", "—")))
        self.console.print(table)
        self.console.print()

    def _show_agent_info(self):
        """Show current agent info."""
        table = Table(title="Agent Configuration", box=box.ROUNDED)
        table.add_column("Параметр", style="bold")
        table.add_column("Значение", style="")
        table.add_row("ID", self.agent_id)
        table.add_row("Name", self.agent_config.get("name", "—"))
        table.add_row("Role", self.agent_config.get("role", "—"))
        table.add_row("Skills", str(len(self.agent_config.get("skills", []))))
        table.add_row("Tools", str(len(self.agent_config.get("tools", []))))
        self.console.print(table)
        self.console.print()

    def _show_status(self):
        """Show system status."""
        agents = self.store.list_agents()
        table = Table(title=self._t("status_title"), box=box.ROUNDED)
        table.add_column("Метрика", style="bold")
        table.add_column("Значение", style="")
        table.add_row("Агентов", str(len(agents)))
        table.add_row("Навыков", str(sum(len(a.get("skills", [])) for a in agents)))
        table.add_row("Инструментов", str(sum(len(a.get("tools", [])) for a in agents)))
        table.add_row("Сессия", self.session_id[:20])
        table.add_row("Сообщений", str(self.message_count))
        table.add_row("Средняя задержка", f"{self.total_latency / max(self.message_count, 1):.1f}s")
        self.console.print(table)
        self.console.print()

    # ------------------------------------------------------------------
    # Main Loop
    # ------------------------------------------------------------------

    async def process_message(self, text: str) -> str:
        """Send message to agent and return response."""
        self.render_thinking()

        start = time.time()
        try:
            result = await self.agent.run(text, session_id=self.session_id)
            latency = time.time() - start
            self.total_latency += latency
            self.message_count += 1
            return str(result), latency
        except Exception as e:
            latency = time.time() - start
            return f"[Ошибка: {str(e)[:200]}]", latency

    def run_chat_loop(self):
        """Run interactive chat loop."""
        self.console.clear()
        self.render_welcome()
        self._create_session()

        while True:
            try:
                # Status bar
                self.render_status_bar()

                # Input prompt — use raw stdin to avoid Windows CP1251 issues
                self.console.print(f"[bold blue]{self._t('you')}[/] › ", end="")
                user_input = sys.stdin.buffer.readline().decode('utf-8').strip()
            except (EOFError, KeyboardInterrupt):
                self.console.print(f"\n[dim]{self._t('goodbye')}[/]")
                break

            if not user_input:
                continue

            # Slash command?
            if user_input.startswith("/"):
                if not self.handle_command(user_input):
                    break
                continue

            # Render user message
            self.render_user_message(user_input)
            self._save_message("user", user_input)
            self.messages.append({"role": "user", "content": user_input})

            # Process
            self.render_thinking()
            result, latency = asyncio.run(self.process_message(user_input))

            # Render response
            self.render_assistant_message(result, latency)
            self._save_message("assistant", result)
            self.messages.append({"role": "assistant", "content": result})

        # Cleanup
        self.state_db.close()


def run_tui(agent_id: str = "universal", model: str = "fast", session_id: Optional[str] = None):
    """Entry point for CLI TUI."""
    tui = AgentTUI(agent_id=agent_id, model_profile=model, session_id=session_id)
    tui.run_chat_loop()
