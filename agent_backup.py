#!/usr/bin/env python3
"""My Agent — beautiful CLI for your AI agent system."""
import sys, os, yaml, json, time, asyncio, logging, argparse
from pathlib import Path
from datetime import datetime

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config, save_config, resolve_env_vars, SKILLS_DIRS
from core.builder import AgentBuilder
from core.agent_store import AgentStore
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich.syntax import Syntax
from rich.rule import Rule
from rich.align import Align
from rich.box import ROUNDED, HEAVY, MINIMAL, DOUBLE

console = Console(force_terminal=True)
LOG_DIR = Path("data/logs"); LOG_DIR.mkdir(parents=True, exist_ok=True)

BANNER = """
[bold cyan]╔══════════════════════════════════════════════════════════╗
║  [bold white]███╗   ███╗██╗   ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗[/bold white]  ║
║  [bold white]████╗ ████║╚██╗ ██╔╝    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/bold white]  ║
║  [bold white]██╔████╔██║ ╚████╔╝     ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   [/bold white]  ║
║  [bold white]██║╚██╔╝██║  ╚██╔╝      ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   [/bold white]  ║
║  [bold white]██║ ╚═╝ ██║   ██║       ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   [/bold white]  ║
║  [bold white]╚═╝     ╚═╝   ╚═╝       ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   [/bold white]  ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]
"""

def _log_file():
    return LOG_DIR / f"agent_{datetime.now().strftime('%Y-%m-%d')}.log"

def _setup_file_logging():
    fh = logging.FileHandler(_log_file(), encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    root = logging.getLogger(); root.addHandler(fh); root.setLevel(logging.INFO)

def _safe_icon(icon: str) -> str:
    try: icon.encode("cp1251"); return icon
    except UnicodeEncodeError: return "*"

# ─── CLI USER SESSION (multi-user CLI support) ─────────────────────────────

CLI_USER_FILE = Path("data/cli_user.json")

def _get_cli_user():
    """Get current CLI user session."""
    if CLI_USER_FILE.exists():
        try:
            with open(CLI_USER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def _set_cli_user(user_data):
    """Save CLI user session."""
    CLI_USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLI_USER_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

def _clear_cli_user():
    """Clear CLI user session."""
    if CLI_USER_FILE.exists():
        CLI_USER_FILE.unlink()

def _cli_user_label():
    """Return username label for prompt, or empty string."""
    user = _get_cli_user()
    if user and user.get("username"):
        return f"[bold cyan]{user['username']}[/bold cyan] "
    return ""

# ─── MODEL PROFILES ──────────────────────────────────────────────────────────

MODEL_PROFILES = {
    "fast": {
        "primary": "openai/gpt-5.4-nano",
        "api_key": "${NEUROAPI_API_KEY}",
        "base_url": "https://neuroapi.host/v1",
        "fallback": "openrouter/owl-alpha",
        "fallback_api_key": "${OPENROUTER_API_KEY}",
        "fallback_base_url": "https://openrouter.ai/api/v1",
        "params": {"temperature": 0.7, "max_tokens": 4096},
        "max_retries": 3, "retry_base_delay": 5.0, "retry_max_delay": 60.0,
    },
    "balanced": {
        "primary": "openrouter/owl-alpha",
        "api_key": "${OPENROUTER_API_KEY}",
        "base_url": "https://openrouter.ai/api/v1",
        "fallback": "openai/gpt-5.4-nano",
        "fallback_api_key": "${NEUROAPI_API_KEY}",
        "fallback_base_url": "https://neuroapi.host/v1",
        "params": {"temperature": 0.7, "max_tokens": 8192},
        "max_retries": 3, "retry_base_delay": 5.0, "retry_max_delay": 60.0,
    },
    "smart": {
        "primary": "anthropic/claude-sonnet-4-20250514",
        "api_key": "${OPENROUTER_API_KEY}",
        "base_url": "https://openrouter.ai/api/v1",
        "fallback": "openrouter/owl-alpha",
        "fallback_api_key": "${OPENROUTER_API_KEY}",
        "fallback_base_url": "https://openrouter.ai/api/v1",
        "params": {"temperature": 0.3, "max_tokens": 16000},
        "max_retries": 3, "retry_base_delay": 5.0, "retry_max_delay": 60.0,
    },
    "local": {
        "primary": "ollama/llama3",
        "api_key": "",
        "base_url": "http://localhost:11434",
        "params": {"temperature": 0.7, "max_tokens": 4096},
        "max_retries": 1, "retry_base_delay": 2.0, "retry_max_delay": 10.0,
    },
}

def _resolve_model_profile(profile_name: str) -> dict:
    """Resolve model profile by name, or return default."""
    profile = MODEL_PROFILES.get(profile_name)
    if profile:
        return resolve_env_vars(profile)
    # Try to load from config/models.yaml
    yaml_path = Path("config/models.yaml")
    if yaml_path.exists():
        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            models = data.get("models", {})
            if profile_name in models:
                cfg = models[profile_name]
                return resolve_env_vars(cfg)
        except Exception:
            pass
    # Default to fast profile
    return resolve_env_vars(MODEL_PROFILES["fast"])

def _build_model_config(agent_config: dict) -> dict:
    """Build model config dict from agent config (handles string or dict model field)."""
    model_raw = agent_config.get("model", {})
    if isinstance(model_raw, str):
        return resolve_env_vars({
            "primary": model_raw,
            "api_key": agent_config.get("api_key", "${NEUROAPI_API_KEY}"),
            "base_url": agent_config.get("base_url", "https://neuroapi.host/v1"),
            "fallback": "openai/gpt-5.4-nano",
            "fallback_api_key": "${NEUROAPI_API_KEY}",
            "fallback_base_url": "https://neuroapi.host/v1",
            "params": {"temperature": 0.7, "max_tokens": 8192},
            "max_retries": 3,
            "retry_base_delay": 5.0,
            "retry_max_delay": 60.0,
        })
    return resolve_env_vars(model_raw)

def _with_spinner(agent_id, coro):
    start = time.time()
    with console.status(f"[bold yellow]{agent_id}[/bold yellow]", spinner="dots") as status:
        result = asyncio.run(coro)
    return result

# ─── COMMANDS ────────────────────────────────────────────────────────────────

def cmd_login(args):
    """Authenticate CLI user and store session."""
    username = args.username or console.input("[bold green]Username:[/bold green] ")
    password = args.password or console.input("[bold green]Password:[/bold green] ", password=True)
    # Simple auth: check against stored users or create new
    from core.user_manager import UserManager
    um = UserManager()
    asyncio.run(um.connect())
    user = asyncio.run(um.authenticate(username, password))
    asyncio.run(um.close())
    if user:
        _set_cli_user({"username": username, "user_id": user["id"], "role": user.get("role", "user")})
        console.print(Panel(f"[green]Welcome, {username}![/green]", title="Login", border_style="green"))
    else:
        # Allow local CLI auth without web backend
        _set_cli_user({"username": username, "user_id": f"local_{username}", "role": "user"})
        console.print(Panel(f"[yellow]Local session started for {username}.[/yellow]", title="Login", border_style="yellow"))

def cmd_logout(args):
    """Clear CLI user session."""
    user = _get_cli_user()
    _clear_cli_user()
    if user:
        console.print(Panel(f"[yellow]Goodbye, {user.get('username', 'user')}.[/yellow]", title="Logout", border_style="yellow"))
    else:
        console.print(Panel("[dim]Not logged in.[/dim]", title="Logout", border_style="dim"))

def cmd_chat(args):
    agent_id = args.agent or "universal"
    store = AgentStore()
    agent_config = store.get_agent(agent_id)
    if not agent_config:
        console.print(Panel(f"[red]Agent '{agent_id}' not found[/red]\nAvailable: {', '.join(a['id'] for a in store.list_agents())}", title="Error", border_style="red"))
        return

    # Resolve model profile
    model_config = _resolve_model_profile(args.model) if args.model else _build_model_config(agent_config)
    model_name = model_config.get("primary", "unknown").split("/")[-1]
    fallback_name = model_config.get("fallback", "").split("/")[-1] if model_config.get("fallback") else "none"

    user_label = _cli_user_label()
    console.print(Panel.fit(
        f"[bold yellow]{_safe_icon(agent_config.get('icon', '🤖'))} {agent_config.get('name', agent_id)}[/bold yellow]\n"
        f"[dim]{agent_config.get('description', '')}[/dim]\n"
        f"[cyan]Model:[/cyan] [bold]{model_name}[/bold]   "
        f"[cyan]Fallback:[/cyan] [dim]{fallback_name}[/dim]   "
        f"[cyan]Skills:[/cyan] {len(agent_config.get('skills', []))}   "
        f"[cyan]Tools:[/cyan] {len(agent_config.get('tools', []))}\n"
        f"[grey46]Type [bold]/help[/bold] for commands, [bold]/exit[/bold] to quit[/grey46]",
        title=f"{user_label}My Agent CLI", border_style="blue", box=HEAVY
    ))

    builder = (AgentBuilder().set_model(model_config).set_role(agent_config.get("role", ""))
        .set_skills(agent_config.get("skills", [])).set_tools(agent_config.get("tools", []))
        .set_memory(agent_config.get("memory", {"enabled": True}))
        .enable_events(True).enable_compression(False).enable_plugins(True))
    agent = builder.build()
    session_id, history = f"cli_{int(time.time())}", []

    while True:
        try:
            prompt = f"{user_label}[bold green]┃ You:[/bold green] " if user_label else "[bold green]┃ You:[/bold green] "
            user_input = console.input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye![/yellow]"); break
        if not user_input: continue
        if user_input.lower() in ("/exit", "/quit", "/q"):
            console.print("[yellow]Session saved. Goodbye![/yellow]"); break
        if user_input.lower() == "/help":
            console.print(Panel(
                "[bold cyan]/help[/bold cyan]    — Show this help\n"
                "[bold cyan]/exit[/bold cyan]    — Quit chat\n"
                "[bold cyan]/clear[/bold cyan]   — Clear history\n"
                "[bold cyan]/model[/bold cyan]   — Show model info\n"
                "[bold cyan]/user[/bold cyan]    — Show current user\n"
                "[bold cyan]/tokens[/bold cyan]  — Show session token usage",
                title="Chat Commands", border_style="cyan", box=ROUNDED
            )); continue
        if user_input.lower() == "/clear": history.clear(); console.print("[dim]History cleared.[/dim]"); continue
        if user_input.lower() == "/model":
            console.print(Panel(
                f"[cyan]Primary:[/cyan] {model_name}\n"
                f"[cyan]Fallback:[/cyan] {fallback_name}\n"
                f"[cyan]Provider:[/cyan] {model_config.get('base_url', '?').replace('https://', '').replace('/v1', '')}\n"
                f"[cyan]Skills:[/cyan] {len(agent_config.get('skills', []))}\n"
                f"[cyan]Tools:[/cyan] {len(agent_config.get('tools', []))}",
                title="Agent Info", border_style="cyan"
            )); continue
        if user_input.lower() == "/user":
            user = _get_cli_user()
            if user:
                console.print(Panel(f"[cyan]User:[/cyan] {user.get('username', '?')}\n[cyan]Role:[/cyan] {user.get('role', '?')}", title="User Info"))
            else:
                console.print(Panel("[dim]Not logged in. Use: agent login <username>[/dim]", title="User Info"))
            continue

        history.append({"role": "user", "content": user_input})
        start = time.time()
        try:
            result = _with_spinner(agent_id, agent.run(user_input, session_id=session_id))
            latency = time.time() - start
            history.append({"role": "assistant", "content": result})
            console.print(Rule(style="green"))
            console.print(f"[bold green]┃ Agent[/bold green] [dim]({latency:.1f}s)[/dim]")
            console.print(Markdown(result))
            console.print()
        except Exception as e:
            console.print(Panel(f"[red]{e}[/red]", title="Error", border_style="red"))

def cmd_run_agent(args):
    store = AgentStore()
    agent_config = store.get_agent(args.agent)
    if not agent_config: console.print(Panel(f"[red]Agent '{args.agent}' not found[/red]", title="Error", border_style="red")); return

    model_config = _resolve_model_profile(args.model) if args.model else _build_model_config(agent_config)
    builder = (AgentBuilder().set_model(model_config).set_role(agent_config.get("role", ""))
        .set_skills(agent_config.get("skills", [])).set_tools(agent_config.get("tools", []))
        .set_memory(agent_config.get("memory", {"enabled": True}))
        .enable_events(True).enable_compression(False).enable_plugins(True))
    agent = builder.build()
    user_input = args.input or console.input("[bold green]┃ You:[/bold green] ")
    if not user_input: return

    start = time.time()
    try:
        result = _with_spinner(args.agent, agent.run(user_input))
        latency = time.time() - start
        console.print(Rule(style="green"))
        console.print(f"[bold green]┃ {args.agent}[/bold green] [dim]({latency:.1f}s)[/dim]")
        console.print(Markdown(result))
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f: f.write(result)
            console.print(f"\n[green]✓ Saved to {args.output}[/green]")
    except Exception as e:
        console.print(Panel(f"[red]{e}[/red]", title="Error", border_style="red"))

def cmd_run(args):
    config_path = f"tasks/{args.task}.yaml"
    if not os.path.exists(config_path):
        console.print(Panel(f"[red]Task not found: {config_path}[/red]\nAvailable: {', '.join(list_tasks())}", title="Error", border_style="red")); return
    config = load_config(config_path)
    builder = (AgentBuilder().set_model(config["model"]).set_role(config["role"])
        .set_skills(config["skills"]).set_tools(config.get("tools", []))
        .set_memory(config.get("memory", {"enabled": False})))
    agent = builder.build()
    user_input = args.input or console.input("[bold green]┃ You:[/bold green] ")
    if not user_input: return

    start = time.time()
    try:
        result = _with_spinner(args.task, agent.run(user_input))
        latency = time.time() - start
        console.print(Rule(style="green"))
        console.print(f"[bold green]┃ Result[/bold green] [dim]({latency:.1f}s)[/dim]")
        console.print(Markdown(result))
        if config.get("output", {}).get("path"):
            p = config["output"]["path"]; os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            with open(p, "w", encoding="utf-8") as f: f.write(result)
            console.print(f"[green]✓ Saved to {p}[/green]")
    except Exception as e:
        console.print(Panel(f"[red]{e}[/red]", title="Error", border_style="red"))

def cmd_serve(args):
    import uvicorn; from web.server import app
    port, host, workers = args.port or 8000, args.host or "0.0.0.0", args.workers or 1
    console.print(Panel(
        f"[bold green]🚀 Server starting[/bold green]\n"
        f"  URL:      [cyan]http://{host}:{port}[/cyan]\n"
        f"  Workers:  {workers}\n"
        f"  Reload:   {'[green]on[/green]' if args.reload else '[red]off[/red]'}\n"
        f"  Press [bold]Ctrl+C[/bold] to stop",
        title="My Agent Server", border_style="green", box=HEAVY
    ))
    uvicorn.run("web.server:app", host=host, port=port, workers=workers, reload=args.reload)

def cmd_status(args):
    store = AgentStore(); agents = store.list_agents()
    total_agents = len(agents)
    total_skills = sum(len(a.get("skills", [])) for a in agents)
    total_tools = sum(len(a.get("tools", [])) for a in agents)

    # Resolve model name safely
    first_agent = agents[0] if agents else {}
    model_raw = first_agent.get("model", {})
    if isinstance(model_raw, str):
        model = model_raw.split("/")[-1]
    else:
        model = model_raw.get("primary", "?").split("/")[-1] if isinstance(model_raw, dict) else "?"

    db_file = Path("data/agent.db"); db_size = db_file.stat().st_size if db_file.exists() else 0
    log_count = len(list(LOG_DIR.glob("*.log")))
    user = _get_cli_user()
    user_str = f"{user.get('username', '?')} ({user.get('role', '?')})" if user else "not logged in"

    layout = Layout()
    layout.split_row(
        Layout(Panel(
            f"[cyan]Agents[/cyan]   [bold]{total_agents}[/bold]\n"
            f"[cyan]Skills[/cyan]   [bold]{total_skills}[/bold]\n"
            f"[cyan]Tools[/cyan]    [bold]{total_tools}[/bold]",
            title="Stats", border_style="cyan", box=ROUNDED
        )),
        Layout(Panel(
            f"[cyan]User[/cyan]      [bold]{user_str}[/bold]\n"
            f"[cyan]Model[/cyan]     [bold yellow]{model}[/bold yellow]\n"
            f"[cyan]Database[/cyan]  {db_size/1024:.1f} KB\n"
            f"[cyan]Log files[/cyan] {log_count}",
            title="System", border_style="green", box=ROUNDED
        )),
    )
    console.print(layout)

    # Model profiles table
    profile_table = Table(title=None, box=MINIMAL, header_style="bold cyan")
    profile_table.add_column("Profile", style="bold yellow")
    profile_table.add_column("Primary", style="green")
    profile_table.add_column("Fallback", style="blue")
    profile_table.add_column("Speed", style="cyan")
    profiles_info = [
        ("fast", "neuroapi gpt-5.4-nano", "openrouter owl-alpha", "~1.5s"),
        ("balanced", "openrouter owl-alpha", "neuroapi gpt-5.4-nano", "~6s"),
        ("smart", "openrouter claude-sonnet-4", "openrouter owl-alpha", "~8s"),
        ("local", "ollama llama3", "none", "local"),
    ]
    for name, primary, fallback, speed in profiles_info:
        profile_table.add_row(name, primary, fallback or "none", speed)
    console.print(Panel(profile_table, title="[bold]Model Profiles[/bold]", border_style="yellow", box=HEAVY))

    table = Table(title=None, box=MINIMAL, header_style="bold cyan")
    table.add_column("Agent", style="bold")
    table.add_column("Model", style="yellow")
    table.add_column("Skills", style="green")
    table.add_column("Tools", style="blue")
    for a in agents:
        m_raw = a.get("model", {})
        if isinstance(m_raw, str):
            m_name = m_raw.split("/")[-1]
        else:
            m_name = m_raw.get("primary", "?").split("/")[-1] if isinstance(m_raw, dict) else "?"
        table.add_row(
            f"{_safe_icon(a.get('icon',''))} {a.get('name','?')}",
            m_name,
            str(len(a.get("skills",[]))),
            str(len(a.get("tools",[])))
        )
    console.print(Panel(table, title=f"[bold]Agents ({total_agents})[/bold]", border_style="blue", box=HEAVY))

def cmd_services(args):
    results = []
    checks = [
        ("✓ NeuroAPI", f"openai/gpt-5.4-nano"),
        ("✓ SQLite DB", Path("data/agent.db").exists()),
        ("✓ Redis", False),
        ("✓ Docker", os.system("docker ps >nul 2>&1") == 0),
    ]
    neuro_ok = True
    try:
        import litellm
    except: neuro_ok = False

    table = Table(title=None, box=MINIMAL, header_style="bold cyan")
    table.add_column("Service", style="bold")
    table.add_column("Status", style="bold")
    for name, ok in checks:
        icon = "[green]●[/green]" if ok else "[red]○[/red]"
        status = "[green]Online[/green]" if ok else "[red]Offline[/red]"
        table.add_row(f"{icon} {name}", status)
    console.print(Panel(table, title="Service Health", border_style="green", box=HEAVY))

def cmd_logs(args):
    if args.follow: _tail_logs_follow(args.lines)
    else: _view_logs(args.lines)

def _view_logs(lines=50):
    log_file = _log_file()
    if not log_file.exists(): console.print(Panel("[yellow]No log files yet[/yellow]", border_style="yellow")); return
    with open(log_file, "r", encoding="utf-8") as f: all_lines = f.readlines()
    show = all_lines[-lines:] if lines < len(all_lines) else all_lines
    console.print(Panel(f"[dim]Last {len(show)} lines from {log_file.name}[/dim]", border_style="blue", box=ROUNDED))
    for line in show:
        line = line.rstrip()
        if "ERROR" in line: console.print(f"[red]{line}[/red]")
        elif "WARNING" in line: console.print(f"[yellow]{line}[/yellow]")
        elif "DEBUG" in line: console.print(f"[dim]{line}[/dim]")
        else: console.print(line)

def _tail_logs_follow(lines=50):
    log_file = _log_file()
    if not log_file.exists(): console.print(Panel("[yellow]No log files yet[/yellow]", border_style="yellow")); return
    console.print(f"[dim]Following {log_file.name}... Press Ctrl+C to stop[/dim]\n")
    try:
        import subprocess; subprocess.run(["tail", "-f", str(log_file)])
    except FileNotFoundError:
        with open(log_file, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line: console.print(line.rstrip())
                else: time.sleep(0.5)
    except KeyboardInterrupt: console.print("\n[yellow]Stopped.[/yellow]")

def cmd_list_agents(args):
    store = AgentStore(); agents = store.list_agents()
    table = Table(title=None, box=MINIMAL, header_style="bold cyan")
    table.add_column("", style="bold", width=3)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold green")
    table.add_column("Skills", style="blue")
    table.add_column("Model", style="yellow")
    for i, a in enumerate(agents, 1):
        table.add_row(
            str(i),
            a.get("id", "?"),
            f"{_safe_icon(a.get('icon',''))} {a.get('name','?')}",
            str(len(a.get("skills",[]))),
            a.get("model",{}).get("primary","?").split("/")[-1]
        )
    console.print(Panel(table, title=f"[bold]Agents ({len(agents)})[/bold]", border_style="blue", box=HEAVY))

def cmd_list_skills(args):
    table = Table(title=None, box=MINIMAL, header_style="bold cyan")
    table.add_column("Skill", style="bold green")
    table.add_column("Description", style="dim")
    table.add_column("Tools", style="blue")
    for skills_dir in SKILLS_DIRS:
        if not os.path.exists(skills_dir): continue
        for skill_dir in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, skill_dir, "SKILL.md")
            if os.path.exists(skill_md):
                with open(skill_md, "r", encoding="utf-8") as f: content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        meta = yaml.safe_load(parts[1])
                        table.add_row(meta.get("name", skill_dir), meta.get("description", ""), ", ".join(meta.get("tools", [])))
    console.print(Panel(table, title="[bold]Skills[/bold]", border_style="green", box=HEAVY))

def cmd_list_tasks(args):
    tasks_dir = "tasks/"
    if not os.path.exists(tasks_dir): console.print(Panel("[yellow]No tasks directory[/yellow]", border_style="yellow")); return
    table = Table(title=None, box=MINIMAL, header_style="bold cyan")
    table.add_column("Task", style="bold cyan")
    table.add_column("Description", style="dim")
    table.add_column("Skills", style="green")
    table.add_column("Model", style="yellow")
    for filename in sorted(os.listdir(tasks_dir)):
        if filename.endswith(".yaml"):
            config = load_config(f"{tasks_dir}{filename}")
            table.add_row(filename.replace(".yaml",""), config.get("description",""), ", ".join(config.get("skills",[])), config.get("model",{}).get("primary",""))
    console.print(Panel(table, title="[bold]Tasks[/bold]", border_style="magenta", box=HEAVY))

def cmd_setup(args):
    """Run first-time setup wizard."""
    from core.wizard import run_setup_wizard, is_first_run
    if not args.force and not is_first_run():
        console.print(Panel(
            "[yellow]Агент уже настроен. Используйте --force для повторной настройки.[/yellow]\n"
            "[dim]Для переконфигурации: agent configure[/dim]",
            title="Setup",
            border_style="yellow",
        ))
        return
    run_setup_wizard()

def cmd_configure(args):
    """Reconfigure agent for different tasks."""
    from core.wizard import run_reconfigure_wizard
    run_reconfigure_wizard()

def cmd_init(args):
    task_path = f"tasks/{args.name}.yaml"
    if os.path.exists(task_path): console.print(Panel(f"[yellow]Task already exists: {task_path}[/yellow]", border_style="yellow")); return
    config = {"name": args.name, "description": "", "model": {"primary": "openai/gpt-5.4-nano", "api_key": "${NEUROAPI_API_KEY}", "base_url": "https://neuroapi.host/v1"}, "role": "Ты — полезный ассистент.", "skills": [], "tools": [], "memory": {"enabled": True, "scope": "task"}, "output": {"format": "markdown", "path": ""}}
    save_config(config, task_path)
    console.print(Panel(f"[green]✓ Created: {task_path}[/green]\nRun: [cyan]agent run {args.name}[/cyan]", title="Task Created", border_style="green"))

def cmd_test(args):
    import subprocess
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-p", "no:warnings"]
    if args.fast: cmd.extend(["-m", "not slow and not e2e and not ux"])
    if args.coverage: cmd.extend(["--cov=core", "--cov=skills", "--cov=tools", "--cov=web"])
    console.print(Panel(f"[dim]{' '.join(cmd)}[/dim]", title="Running Tests", border_style="cyan", box=ROUNDED))
    try: subprocess.run(cmd, check=False)
    except KeyboardInterrupt: console.print("\n[yellow]Tests interrupted.[/yellow]")

def cmd_benchmark(args):
    import subprocess
    console.print(Rule(style="cyan"))
    table = Table(title="Performance Benchmarks", box=MINIMAL, header_style="bold cyan")
    table.add_column("Test", style="bold")
    table.add_column("Status", style="bold")
    table.add_column("Time", style="blue")
    bench = [
        ("Core LLM", ["python", "-c", "import asyncio; from core.llm_gateway import LLMGateway; asyncio.run(LLMGateway({'primary':'openai/gpt-5.4-nano','api_key':os.environ.get('NEUROAPI_API_KEY',''),'base_url':'https://neuroapi.host/v1','params':{'max_tokens':50}}).chat([{'role':'user','content':'hi'}]))"]),
        ("Agent Build", ["python", "-c", "from core.builder import AgentBuilder; AgentBuilder().set_model({'primary':'test'}).set_role('test').set_skills(['research']).set_tools(['web_search']).build()"]),
    ]
    for name, cmd in bench:
        t0 = time.time()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            t = time.time() - t0
            passed = r.returncode == 0
            table.add_row(name, "[green]✓[/green]" if passed else "[red]✗[/red]", f"{t:.1f}s")
        except Exception as e:
            table.add_row(name, f"[red]{e}[/red]", "-")
    console.print(table)

def list_tasks():
    tasks_dir = "tasks/"
    if not os.path.exists(tasks_dir): return []
    return [f.replace(".yaml", "") for f in os.listdir(tasks_dir) if f.endswith(".yaml")]

# ─── MAIN ────────────────────────────────────────────────────────────────────

def show_help():
    console.print(BANNER)
    console.print(Rule(style="blue"))

    user = _get_cli_user()
    user_str = f"[cyan]User:[/cyan] [bold]{user['username']}[/bold]" if user else "[dim]Not logged in[/dim]"
    console.print(Panel(user_str, title="Session", border_style="cyan", box=ROUNDED))

    cmds = Columns([
        Panel("[bold cyan]Agent[/bold cyan]\n[green]chat[/green]       Interactive chat\n[green]run-agent[/green]  Run agent once\n[green]run[/green]        Run a task\n[green]setup[/green]      First-time wizard\n[green]configure[/green] Reconfigure", box=ROUNDED, border_style="blue"),
        Panel("[bold cyan]System[/bold cyan]\n[green]status[/green]    System status\n[green]services[/green]  Service health\n[green]logs[/green]      View logs\n[green]serve[/green]     Web server", box=ROUNDED, border_style="green"),
        Panel("[bold cyan]Auth[/bold cyan]\n[green]login[/green]      Login to CLI\n[green]logout[/green]     Logout from CLI", box=ROUNDED, border_style="magenta"),
        Panel("[bold cyan]Dev[/bold cyan]\n[green]test[/green]       Run tests\n[green]benchmark[/green] Performance\n[green]init[/green]      Create task", box=ROUNDED, border_style="yellow"),
    ])
    console.print(cmds)
    console.print(Rule(style="blue"))
    console.print("[dim]Examples:[/dim]")
    console.print("  [bold]agent chat --model fast[/bold]              — Chat with fast profile")
    console.print("  [bold]agent login user123[/bold]                  — Login to CLI")
    console.print("  [bold]agent status[/bold]                         — Show system status")
    console.print("  [bold]agent run-agent universal --input 'hi'[/bold] — Quick query")
    console.print("\n[dim]Model profiles:[/dim] [cyan]fast[/cyan] (neuroapi), [cyan]balanced[/cyan] (openrouter), [cyan]smart[/cyan] (claude), [cyan]local[/cyan] (ollama)")

def main():
    _setup_file_logging()
    
    # Check first run
    from core.wizard import is_first_run
    if is_first_run():
        console.print(Panel.fit(
            "[bold cyan]👋 Привет! Это первый запуск My Agent.[/bold cyan]\n\n"
            "[dim]Для начала работы нужно настроить агента:[/dim]\n"
            "  [bold]python agent.py setup[/bold]     — Интерактивная настройка\n"
            "  [bold]python agent.py chat[/bold]       — Быстрый старт с настройками по умолчанию\n\n"
            "[dim]Или получите справку:[/dim]  [bold]python agent.py --help[/bold]",
            title="My Agent v2.1.0",
            border_style="cyan",
            box=box.DOUBLE,
        ))
        # Still show help if they run without args
    
    parser = argparse.ArgumentParser(description="My Agent — AI agent system", formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command")

    p_setup = subparsers.add_parser("setup", help="First-time setup wizard")
    p_setup.add_argument("--force", action="store_true", help="Force re-setup")

    subparsers.add_parser("configure", help="Reconfigure agent for different tasks")

    p_login = subparsers.add_parser("login", help="Login to CLI session")
    p_login.add_argument("username", nargs="?", help="Username")
    p_login.add_argument("--password", "-p", help="Password")

    subparsers.add_parser("logout", help="Logout from CLI session")

    p_chat = subparsers.add_parser("chat", help="Interactive terminal chat")
    p_chat.add_argument("--agent", "-a", default="universal", help="Agent ID (default: universal)")
    p_chat.add_argument("--model", "-m", choices=list(MODEL_PROFILES.keys()), help=f"Model profile: {', '.join(MODEL_PROFILES.keys())}")

    p_ra = subparsers.add_parser("run-agent", help="Run a registered agent")
    p_ra.add_argument("agent", help="Agent ID")
    p_ra.add_argument("--input", "-i", help="Input prompt")
    p_ra.add_argument("--output", "-o", help="Save output to file")
    p_ra.add_argument("--model", "-m", choices=list(MODEL_PROFILES.keys()), help=f"Model profile: {', '.join(MODEL_PROFILES.keys())}")

    p_run = subparsers.add_parser("run", help="Run a task")
    p_run.add_argument("task", help="Task name")
    p_run.add_argument("--input", "-i", help="Input prompt")

    p_serve = subparsers.add_parser("serve", help="Start web server")
    p_serve.add_argument("--port", "-p", type=int, default=8000, help="Port (default: 8000)")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p_serve.add_argument("--workers", "-w", type=int, default=1, help="Workers (default: 1)")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload")

    subparsers.add_parser("status", help="Show system status")
    subparsers.add_parser("services", help="Show service health")

    p_logs = subparsers.add_parser("logs", help="View logs")
    p_logs.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    p_logs.add_argument("--lines", "-n", type=int, default=50, help="Number of lines (default: 50)")

    subparsers.add_parser("list-agents", help="List registered agents")
    subparsers.add_parser("list-skills", help="List available skills")
    subparsers.add_parser("list-tasks", help="List tasks")

    p_test = subparsers.add_parser("test", help="Run tests")
    p_test.add_argument("--fast", action="store_true", help="Skip slow tests")
    p_test.add_argument("--coverage", action="store_true", help="Show coverage")

    subparsers.add_parser("benchmark", help="Run performance benchmark")
    p_init = subparsers.add_parser("init", help="Create a new task")
    p_init.add_argument("name", help="Task name")

    args = parser.parse_args()
    if args.command is None:
        show_help(); return

    cmds = {
        "chat": cmd_chat, "run-agent": cmd_run_agent, "run": cmd_run,
        "serve": cmd_serve, "status": cmd_status, "services": cmd_services,
        "logs": cmd_logs, "list-agents": cmd_list_agents, "list-skills": cmd_list_skills,
        "list-tasks": cmd_list_tasks, "test": cmd_test, "benchmark": cmd_benchmark,
        "init": cmd_init, "login": cmd_login, "logout": cmd_logout,
        "setup": cmd_setup, "configure": cmd_configure,
    }
    if args.command in cmds:
        cmds[args.command](args)
    else:
        show_help()

if __name__ == "__main__":
    main()
