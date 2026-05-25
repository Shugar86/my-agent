#!/usr/bin/env python3
"""
My Agent — Modern Stylish CLI Interface
=====================================
Inspired by OpenCode and Claude Code, but more stylish.
Uses Rich for modern terminal UI with gradients, animations, and sleek design.
"""
import sys
import os
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich.box import ROUNDED, HEAVY, MINIMAL, DOUBLE, SQUARE
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.status import Status
from rich import box
from rich.style import Style
from rich.color import Color

console = Console(force_terminal=True, color_system="auto")
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Modern color palette
COLORS = {
    "primary": "#6366f1",      # Indigo
    "secondary": "#8b5cf6",    # Violet
    "accent": "#ec4899",       # Pink
    "success": "#10b981",      # Emerald
    "warning": "#f59e0b",      # Amber
    "error": "#ef4444",        # Red
    "info": "#3b82f6",         # Blue
    "bg": "#0f172a",           # Slate 900
    "surface": "#1e293b",      # Slate 800
    "text": "#f8fafc",         # Slate 50
    "muted": "#94a3b8",        # Slate 400
}


def gradient_text(text: str, start_color: str = "#6366f1", end_color: str = "#ec4899") -> Text:
    """Create gradient text effect."""
    result = Text()
    length = len(text)
    for i, char in enumerate(text):
        if char == " ":
            result.append(" ")
            continue
        # Interpolate color
        ratio = i / max(length - 1, 1)
        r = int(int(start_color[1:3], 16) * (1 - ratio) + int(end_color[1:3], 16) * ratio)
        g = int(int(start_color[3:5], 16) * (1 - ratio) + int(end_color[3:5], 16) * ratio)
        b = int(int(start_color[5:7], 16) * (1 - ratio) + int(end_color[5:7], 16) * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        result.append(char, style=f"bold {color}")
    return result


def modern_banner() -> Panel:
    """Create modern gradient banner."""
    title = gradient_text("My Agent", "#6366f1", "#ec4899")
    subtitle = Text("AI-powered automation system", style="dim #94a3b8")
    version = Text("v2.1.0", style="bold #6366f1")
    
    content = Text.assemble(
        title, Text("  "), version, "\n",
        subtitle
    )
    
    return Panel(
        content,
        box=box.ROUNDED,
        border_style="#6366f1",
        padding=(1, 2),
        title="[bold #6366f1]◈[/bold #6366f1]",
        title_align="right"
    )


def modern_panel(title: str, content: str, border_color: str = "#6366f1", icon: str = "•") -> Panel:
    """Create modern styled panel."""
    return Panel(
        content,
        box=box.ROUNDED,
        border_style=border_color,
        title=f"[bold {border_color}]{icon} {title}[/bold {border_color}]",
        title_align="left",
        padding=(1, 2)
    )


def spinner_task(description: str, coro):
    """Run async task with modern spinner."""
    with console.status(
        f"[bold {COLORS['primary']}]{description}[/bold {COLORS['primary']}]",
        spinner="dots12",
        spinner_style=COLORS["primary"]
    ):
        return asyncio.run(coro)


def progress_bar(description: str, total: int = 100):
    """Create modern progress bar."""
    return Progress(
        SpinnerColumn(style=COLORS["primary"]),
        TextColumn(f"[bold {COLORS['primary']}]{{task.description}}[/bold {COLORS['primary']}]"),
        BarColumn(
            bar_width=40,
            style=f"#{COLORS['muted'][1:]}",
            complete_style=f"#{COLORS['primary'][1:]}",
            finished_style=f"#{COLORS['success'][1:]}"
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )


def styled_table(title: str, columns: list) -> Table:
    """Create modern styled table."""
    table = Table(
        title=f"[bold {COLORS['primary']}]{title}[/bold {COLORS['primary']}]",
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        header_style=f"bold {COLORS['primary']}",
        row_styles=["", f"dim {COLORS['muted']}"],
        padding=(0, 1)
    )
    for col in columns:
        table.add_column(col["name"], style=col.get("style", ""), justify=col.get("justify", "left"))
    return table


def chat_message(role: str, content: str, model: Optional[str] = None, latency: Optional[float] = None):
    """Display modern chat message."""
    if role == "user":
        # User message - right aligned, accent color
        header = Text.assemble(
            Text("◆ You", style=f"bold {COLORS['accent']}"),
            Text(f"  {datetime.now().strftime('%H:%M')}", style=f"dim {COLORS['muted']}")
        )
        panel = Panel(
            content,
            box=box.ROUNDED,
            border_style=COLORS["accent"],
            title=header,
            title_align="right",
            padding=(1, 2)
        )
    else:
        # Agent message - left aligned, primary color
        header_parts = [Text("◈ Agent", style=f"bold {COLORS['primary']}")]
        if model:
            header_parts.append(Text(f"  {model}", style=f"dim {COLORS['secondary']}"))
        if latency:
            header_parts.append(Text(f"  {latency:.1f}s", style=f"dim {COLORS['muted']}"))
        header = Text.assemble(*header_parts)
        
        panel = Panel(
            Markdown(content),
            box=box.ROUNDED,
            border_style=COLORS["primary"],
            title=header,
            title_align="left",
            padding=(1, 2)
        )
    
    console.print(panel)


def status_panel(active: bool = True, model: str = "fast", provider: str = "neuroapi"):
    """Display modern status panel."""
    status_icon = "🟢" if active else "🔴"
    status_text = "Online" if active else "Offline"
    
    content = Text.assemble(
        Text(f"{status_icon}  ", style="bold"),
        Text(f"{status_text}\n", style=f"bold {COLORS['success'] if active else COLORS['error']}"),
        Text(f"Model: ", style=f"dim {COLORS['muted']}"),
        Text(f"{model}\n", style=f"bold {COLORS['primary']}"),
        Text(f"Provider: ", style=f"dim {COLORS['muted']}"),
        Text(f"{provider}", style=f"bold {COLORS['secondary']}")
    )
    
    return Panel(
        content,
        box=box.ROUNDED,
        border_style=COLORS["success"] if active else COLORS["error"],
        title=f"[bold {COLORS['primary']}]⚡ Status[/bold {COLORS['primary']}]",
        title_align="left",
        padding=(1, 2),
        width=30
    )


def command_palette():
    """Display modern command palette."""
    commands = [
        ("chat", "Interactive chat", COLORS["primary"]),
        ("run-agent", "Run agent", COLORS["secondary"]),
        ("serve", "Start server", COLORS["info"]),
        ("status", "System status", COLORS["success"]),
        ("setup", "First-time setup", COLORS["warning"]),
        ("configure", "Reconfigure", COLORS["accent"]),
        ("login", "Login", COLORS["primary"]),
        ("logout", "Logout", COLORS["muted"]),
        ("test", "Run tests", COLORS["success"]),
        ("benchmark", "Benchmark", COLORS["warning"]),
    ]
    
    table = Table(
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        show_header=False,
        padding=(0, 2)
    )
    table.add_column("Command", style=f"bold {COLORS['primary']}", width=15)
    table.add_column("Description", style=COLORS["text"])
    
    for cmd, desc, color in commands:
        table.add_row(
            f"[bold {color}]{cmd}[/bold {color}]",
            f"[dim {COLORS['muted']}]{desc}[/dim {COLORS['muted']}]"
        )
    
    return Panel(
        table,
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        title=f"[bold {COLORS['primary']}]⌘ Commands[/bold {COLORS['primary']}]",
        title_align="left",
        padding=(1, 2)
    )


# Keep existing imports and functions
def _log_file():
    return LOG_DIR / f"agent_{datetime.now().strftime('%Y-%m-%d')}.log"


def _setup_file_logging():
    fh = logging.FileHandler(_log_file(), encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    root = logging.getLogger()
    root.addHandler(fh)
    root.setLevel(logging.INFO)


def _safe_icon(icon: str) -> str:
    try:
        icon.encode("cp1251")
        return icon
    except UnicodeEncodeError:
        return "*"


# Modern styled commands
def show_modern_help():
    """Display modern help interface."""
    console.print(modern_banner())
    console.print()
    
    # Show status
    from core.agent_store import AgentStore
    store = AgentStore()
    agents = store.list_agents()
    
    stats = Table.grid(padding=2)
    stats.add_column(style=f"bold {COLORS['primary']}")
    stats.add_column(style=COLORS["text"])
    
    stats.add_row("Agents:", f"{len(agents)}")
    stats.add_row("Skills:", f"{sum(len(a.get('skills', [])) for a in agents)}")
    stats.add_row("Tools:", f"{sum(len(a.get('tools', [])) for a in agents)}")
    
    stats_panel = Panel(
        stats,
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        title=f"[bold {COLORS['primary']}]📊 Stats[/bold {COLORS['primary']}]",
        padding=(1, 2),
        width=25
    )
    
    # Show command palette
    cmd_panel = command_palette()
    
    # Layout
    console.print(Columns([stats_panel, cmd_panel], equal=True))
    console.print()
    
    # Examples
    examples = [
        "[dim]# Start interactive chat[/dim]",
        f"[bold {COLORS['primary']}]  agent chat --model fast[/bold {COLORS['primary']}]\n",
        "[dim]# Quick query[/dim]",
        f"[bold {COLORS['primary']}]  agent run-agent universal --input 'hello'[/bold {COLORS['primary']}]\n",
        "[dim]# First-time setup[/dim]",
        f"[bold {COLORS['primary']}]  agent setup[/bold {COLORS['primary']}]",
    ]
    console.print(Panel(
        "\n".join(examples),
        box=box.ROUNDED,
        border_style=COLORS["muted"],
        title=f"[bold {COLORS['muted']}]💡 Examples[/bold {COLORS['muted']}]",
        padding=(1, 2)
    ))


def cmd_chat(args):
    """Modern interactive chat interface."""
    agent_id = args.agent or "universal"
    store = AgentStore()
    agent_config = store.get_agent(agent_id)
    
    if not agent_config:
        console.print(Panel(
            f"[bold {COLORS['error']}]Agent '{agent_id}' not found[/bold {COLORS['error']}]\n"
            f"[dim]Available: {', '.join(a['id'] for a in store.list_agents())}[/dim]",
            title="❌ Error",
            border_style=COLORS["error"]
        ))
        return
    
    model_config = _build_model_config(agent_config)
    model_name = model_config.get("primary", "unknown").split("/")[-1]
    
    # Show modern chat header
    console.print(modern_banner())
    console.print()
    
    # Show agent info
    agent_info = Text.assemble(
        Text(f"{_safe_icon(agent_config.get('icon', '🤖'))} ", style="bold"),
        Text(f"{agent_config.get('name', agent_id)}", style=f"bold {COLORS['primary']}"),
        Text(f"  •  ", style=f"dim {COLORS['muted']}"),
        Text(f"Model: {model_name}", style=f"bold {COLORS['secondary']}"),
        Text(f"  •  ", style=f"dim {COLORS['muted']}"),
        Text(f"Skills: {len(agent_config.get('skills', []))}", style=COLORS["text"]),
        Text(f"  •  ", style=f"dim {COLORS['muted']}"),
        Text(f"Tools: {len(agent_config.get('tools', []))}", style=COLORS["text"])
    )
    
    console.print(Panel(
        agent_info,
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        padding=(1, 2)
    ))
    
    console.print()
    console.print(Rule(style=COLORS["primary"]))
    
    builder = (AgentBuilder().set_model(model_config).set_role(agent_config.get("role", ""))
        .set_skills(agent_config.get("skills", [])).set_tools(agent_config.get("tools", []))
        .set_memory(agent_config.get("memory", {"enabled": True}))
        .enable_events(True).enable_compression(False).enable_plugins(True))
    agent = builder.build()
    
    session_id, history = f"cli_{int(time.time())}", []
    
    while True:
        try:
            # Modern prompt
            user_label = _cli_user_label()
            prompt_text = f"[bold {COLORS['accent']}]◆ You[/bold {COLORS['accent']}]"
            user_input = console.input(f"{prompt_text} ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print(f"\n[dim {COLORS['muted']}]Goodbye! 👋[/dim {COLORS['muted']}]")
            break
        
        if not user_input:
            continue
            
        if user_input.lower() in ("/exit", "/quit", "/q"):
            console.print(f"[dim {COLORS['muted']}]Session saved. Goodbye! 👋[/dim {COLORS['muted']}]")
            break
            
        if user_input.lower() == "/help":
            help_text = """
[bold]Chat Commands:[/bold]
  /help    — Show this help
  /exit    — Quit chat
  /clear   — Clear history
  /model   — Show model info
  /user    — Show current user
  """
            console.print(Panel(help_text, title="Help", border_style=COLORS["primary"]))
            continue
            
        if user_input.lower() == "/clear":
            history.clear()
            console.print(f"[dim {COLORS['muted']}]History cleared 🗑️[/dim {COLORS['muted']}]")
            continue
            
        if user_input.lower() == "/model":
            console.print(status_panel(model=model_name, provider="neuroapi"))
            continue
        
        # Show user message
        chat_message("user", user_input)
        
        # Get response with modern spinner
        start = time.time()
        try:
            with console.status(
                f"[bold {COLORS['primary']}]Agent is thinking...[/bold {COLORS['primary']}]",
                spinner="dots12",
                spinner_style=COLORS["primary"]
            ):
                result = asyncio.run(agent.run(user_input, session_id=session_id))
            
            latency = time.time() - start
            chat_message("agent", result, model=model_name, latency=latency)
            
        except Exception as e:
            console.print(Panel(
                f"[bold {COLORS['error']}]Error:[/bold {COLORS['error']}] {str(e)[:200]}",
                title="❌",
                border_style=COLORS["error"]
            ))


# Import existing functions
from agent import (
    _build_model_config, _resolve_model_profile, _get_cli_user, 
    _set_cli_user, _clear_cli_user, _cli_user_label,
    MODEL_PROFILES, cmd_setup, cmd_configure, cmd_login, cmd_logout,
    cmd_run_agent, cmd_run, cmd_serve, cmd_status, cmd_services,
    cmd_logs, cmd_list_agents, cmd_list_skills, cmd_list_tasks,
    cmd_test, cmd_benchmark, cmd_init
)


def cmd_modern_status(args):
    """Modern status command with visual panels."""
    store = AgentStore()
    agents = store.list_agents()
    
    # Modern header
    console.print(modern_banner())
    console.print()
    
    # Stats grid
    stats = Table.grid(padding=1)
    stats.add_column()
    stats.add_column()
    stats.add_column()
    stats.add_column()
    
    # Agent count panel
    agent_panel = Panel(
        f"[bold {COLORS['primary']}]{len(agents)}[/bold {COLORS['primary']}]\n[dim]agents[/dim]",
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        width=15,
        height=5
    )
    
    skills_count = sum(len(a.get("skills", [])) for a in agents)
    skills_panel = Panel(
        f"[bold {COLORS['secondary']}]{skills_count}[/bold {COLORS['secondary']}]\n[dim]skills[/dim]",
        box=box.ROUNDED,
        border_style=COLORS["secondary"],
        width=15,
        height=5
    )
    
    tools_count = sum(len(a.get("tools", [])) for a in agents)
    tools_panel = Panel(
        f"[bold {COLORS['accent']}]{tools_count}[/bold {COLORS['accent']}]\n[dim]tools[/dim]",
        box=box.ROUNDED,
        border_style=COLORS["accent"],
        width=15,
        height=5
    )
    
    tests_count = 364
    tests_panel = Panel(
        f"[bold {COLORS['success']}]{tests_count}[/bold {COLORS['success']}]\n[dim]tests[/dim]",
        box=box.ROUNDED,
        border_style=COLORS["success"],
        width=15,
        height=5
    )
    
    console.print(Columns([agent_panel, skills_panel, tools_panel, tests_panel]))
    console.print()
    
    # Model profiles table
    console.print(Panel(
        "[bold]Model Profiles[/bold]\n\n"
        f"[bold {COLORS['primary']}]fast[/bold {COLORS['primary']}]      — NeuroAPI (~1.5s)\n"
        f"[bold {COLORS['secondary']}]balanced[/bold {COLORS['secondary']}] — OpenRouter (~6s)\n"
        f"[bold {COLORS['accent']}]smart[/bold {COLORS['accent']}]     — Claude Sonnet (~8s)\n"
        f"[bold {COLORS['muted']}]local[/bold {COLORS['muted']}]     — Ollama (localhost)",
        title="⚡",
        border_style=COLORS["primary"]
    ))


def main():
    """Modern main entry point."""
    _setup_file_logging()
    
    # Check first run
    from core.wizard import is_first_run
    if is_first_run() and len(sys.argv) == 1:
        console.print(modern_banner())
        console.print()
        console.print(Panel(
            f"[bold {COLORS['warning']}]👋 Welcome to My Agent![/bold {COLORS['warning']}]\n\n"
            "[dim]This is your first run. Let's set things up:[/dim]\n\n"
            f"[bold {COLORS['primary']}]  agent setup[/bold {COLORS['primary']}]     — Interactive setup wizard\n"
            f"[bold {COLORS['primary']}]  agent chat[/bold {COLORS['primary']}]      — Quick start with defaults\n"
            f"[bold {COLORS['primary']}]  agent --help[/bold {COLORS['primary']}]    — Show all commands",
            title="First Run",
            border_style=COLORS["warning"]
        ))
        return
    
    parser = argparse.ArgumentParser(
        description="My Agent — AI-powered automation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent setup              First-time configuration
  agent chat --model fast  Interactive chat with fast model
  agent serve              Start web server
  agent status             Show system status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Modern styled commands
    p_chat = subparsers.add_parser("chat", help="Interactive chat with modern UI")
    p_chat.add_argument("--agent", "-a", default="universal", help="Agent ID")
    p_chat.add_argument("--model", "-m", choices=list(MODEL_PROFILES.keys()), help="Model profile")
    
    p_setup = subparsers.add_parser("setup", help="First-time setup wizard")
    p_setup.add_argument("--force", action="store_true", help="Force re-setup")
    
    subparsers.add_parser("configure", help="Reconfigure for different tasks")
    subparsers.add_parser("status", help="Show modern status dashboard")
    
    # Other commands...
    p_run = subparsers.add_parser("run-agent", help="Run agent once")
    p_run.add_argument("agent", help="Agent ID")
    p_run.add_argument("--input", "-i", help="Input prompt")
    p_run.add_argument("--model", "-m", choices=list(MODEL_PROFILES.keys()))
    
    subparsers.add_parser("serve", help="Start web server")
    subparsers.add_parser("login", help="Login to CLI")
    subparsers.add_parser("logout", help="Logout from CLI")
    subparsers.add_parser("test", help="Run tests")
    subparsers.add_parser("benchmark", help="Run benchmark")
    
    args = parser.parse_args()
    
    if args.command is None:
        show_modern_help()
        return
    
    # Route commands
    cmds = {
        "chat": cmd_chat,
        "setup": cmd_setup,
        "configure": cmd_configure,
        "status": cmd_modern_status,
        "run-agent": cmd_run_agent,
        "serve": cmd_serve,
        "login": cmd_login,
        "logout": cmd_logout,
        "test": cmd_test,
        "benchmark": cmd_benchmark,
    }
    
    if args.command in cmds:
        cmds[args.command](args)
    else:
        console.print(f"[bold {COLORS['error']}]Unknown command: {args.command}[/bold {COLORS['error']}]")
        show_modern_help()


if __name__ == "__main__":
    main()
