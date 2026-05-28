#!/usr/bin/env python3
"""My Agent — AI-powered automation system."""
import sys, os, json, time, asyncio, argparse, logging

# Load .env early
from dotenv import load_dotenv
load_dotenv(override=True)
from pathlib import Path
from datetime import datetime
from typing import Optional

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config, resolve_env_vars
from core.configurator import MODEL_PROFILES
from core.builder import AgentBuilder
from core.agent_store import AgentStore
from core.orchestrator import Orchestrator
from core.async_utils import run_coro_sync

import pathlib

# Model profiles — shared with web UI (core/configurator.py)
# Re-exported here for CLI backward compatibility and tests.

# CLI user file (expected by tests)
CLI_USER_FILE = pathlib.Path("data/cli_user.json")

def _get_cli_user():
    if CLI_USER_FILE.exists():
        try:
            return json.loads(CLI_USER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

def _set_cli_user(data):
    CLI_USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLI_USER_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _clear_cli_user():
    if CLI_USER_FILE.exists():
        CLI_USER_FILE.unlink()

def _cli_user_label():
    user = _get_cli_user()
    if user and user.get("username"):
        return f"{user['username']} "
    return ""

def _resolve_model_profile(name):
    from core.config import resolve_env_vars
    profile = MODEL_PROFILES.get(name)
    if profile:
        return resolve_env_vars(profile)
    return resolve_env_vars(MODEL_PROFILES["fast"])

def _build_model_config(agent_config):
    from core.config import resolve_env_vars
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
            "max_retries": 3, "retry_base_delay": 5.0, "retry_max_delay": 60.0,
        })
    return resolve_env_vars(model_raw)

def ensure_dirs():
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure CLI logging with secret redaction on stderr."""
    ensure_dirs()
    from core.logging_setup import setup_logging as setup_core_logging, setup_verbose_logging

    setup_core_logging(mode="agent", log_level="INFO", force=True)
    setup_verbose_logging()

def check_first_run():
    if not Path("config/agent.json").exists():
        print("""
╔══════════════════════════════════════════════════════════════╗
║  Добро пожаловать в My Agent!                                ║
║                                                              ║
║  Это первый запуск. Нужно настроить:                         ║
║                                                              ║
║  1. API ключ OpenRouter (OPENROUTER_API_KEY)                 ║
║  2. Выбрать модель по умолчанию                             ║
║                                                              ║
║  Запусти:  agent setup                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
        return True
    return False

def cmd_setup(args):
    """Interactive setup wizard."""
    print("\n" + "="*60)
    print("  My Agent — First-time Setup")
    print("="*60 + "\n")
    
    name = input("Ваше имя [User]: ").strip() or "User"
    
    print("\nДоступные модели:")
    print("  1. balanced  — OpenRouter owl-alpha (~6с, рекомендуется)")
    print("  2. fast      — NeuroAPI gpt-5.4-nano (~1.5с)")
    print("  3. smart     — Claude Sonnet (~8с)")
    print("  4. local     — Ollama на localhost")
    
    choice = input("\nВыберите модель [1]: ").strip() or "1"
    profiles = {
        "1": ("openrouter/owl-alpha", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
        "2": ("openai/gpt-5.4-nano", "https://neuroapi.host/v1", "NEUROAPI_API_KEY"),
        "3": ("anthropic/claude-sonnet-4", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
        "4": ("ollama/llama3", "http://localhost:11434", None),
    }
    
    model_id, base_url, env_key = profiles.get(choice, profiles["1"])
    
    config = {"user": name}
    
    if env_key:
        key = input(f"\nВведите {env_key}: ").strip()
        if key:
            # Save to .env
            env_path = Path(".env")
            env_lines = []
            if env_path.exists():
                env_lines = env_path.read_text().splitlines()
            # Remove old line if exists
            env_lines = [l for l in env_lines if not l.startswith(f"{env_key}=")]
            env_lines.append(f"{env_key}={key}")
            env_path.write_text("\n".join(env_lines) + "\n")
            print(f"  Ключ сохранён в .env")
            os.environ[env_key] = key
    
    # Save config
    config["model"] = {
        "primary": model_id,
        "api_key": f"${{{env_key}}}" if env_key else "",
        "base_url": base_url,
        "fallback": "openrouter/owl-alpha",
        "fallback_api_key": "${OPENROUTER_API_KEY}",
        "fallback_base_url": "https://openrouter.ai/api/v1",
        "params": {"temperature": 0.7, "max_tokens": 8192},
        "max_retries": 3, "retry_base_delay": 5.0, "retry_max_delay": 60.0,
    }
    
    Path("config").mkdir(exist_ok=True)
    with open("config/agent.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("  Настройка завершена!")
    print(f"  Пользователь: {name}")
    print(f"  Модель: {model_id}")
    print("\n  Запусти: python agent.py chat")
    print("="*60 + "\n")

def cmd_chat(args):
    """Interactive chat with Rich TUI."""
    setup_logging()

    if check_first_run():
        return

    # Use new Rich TUI
    from cli.tui import run_tui
    run_tui(
        agent_id=args.agent or "universal",
        model=args.model or "fast",
        session_id=args.session,
    )

def cmd_status(args):
    """Show system status."""
    store = AgentStore()
    agents = store.list_agents()
    
    print("\n" + "="*60)
    print("  My Agent Status")
    print("="*60)
    print(f"\n  Агентов:      {len(agents)}")
    print(f"  Навыков:      {sum(len(a.get('skills', [])) for a in agents)}")
    print(f"  Инструментов: {sum(len(a.get('tools', [])) for a in agents)}")
    print(f"  Тестов:       376")
    
    print("\n  Агенты:")
    for a in agents:
        print(f"    {a['id']:20} {len(a.get('skills',[]))} skills, {len(a.get('tools',[]))} tools")
    
    print("\n  Модели:")
    print("    fast      — NeuroAPI gpt-5.4-nano")
    print("    balanced  — OpenRouter owl-alpha")
    print("    smart     — Claude Sonnet")
    print("    local     — Ollama llama3")
    print("="*60 + "\n")

def cmd_serve(args):
    """Start web server."""
    import uvicorn
    print("\n" + "="*60)
    print("  Starting Web Server")
    print("="*60)
    print("  URL: http://localhost:8020")
    print("  API: http://localhost:8020/docs")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    uvicorn.run("web.server:app", host="0.0.0.0", port=8020, reload=False)

def cmd_run(args):
    """Run agent once."""
    setup_logging()
    
    if check_first_run():
        return
    
    if not args.input:
        print("Использование: agent run-agent <agent_id> --input 'запрос'")
        return
    
    store = AgentStore()
    agent_config = store.get_agent(args.agent)
    if not agent_config:
        print(f"Агент '{args.agent}' не найден")
        return
    
    config = load_config()
    model_config = resolve_env_vars(config.get("model", {}))
    
    builder = (AgentBuilder()
        .set_model(model_config)
        .set_role(agent_config.get("role", ""))
        .set_skills(agent_config.get("skills", []))
        .set_tools(agent_config.get("tools", []))
        .set_memory({"enabled": False}))
    agent = builder.build()
    
    print(f"\nАгент: {agent_config.get('name', args.agent)}")
    print(f"Запрос: {args.input}\n")
    
    try:
        result = run_coro_sync(agent.run(args.input))
        print(f"\nОтвет:\n{result}")
    except Exception as e:
        print(f"Ошибка: {str(e)[:300]}")

def cmd_test(args):
    """Run tests."""
    import subprocess
    print("Запуск тестов...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-m", 
         "not slow and not docker and not postgres and not e2e and not ux",
         "--tb=short", "-q"],
        capture_output=False,
        text=True
    )
    sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(
        description="My Agent — AI-powered automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python agent.py setup              Первая настройка
  python agent.py chat --model fast  Чат с быстрой моделью
  python agent.py serve              Запустить веб-сервер
  python agent.py status             Статус системы
        """
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Setup
    subparsers.add_parser("setup", help="Первая настройка")
    
    # Chat
    p_chat = subparsers.add_parser("chat", help="Интерактивный чат")
    p_chat.add_argument("--agent", "-a", default="universal")
    p_chat.add_argument("--model", "-m", choices=["fast", "balanced", "smart", "local"])
    p_chat.add_argument("--session", "-s", help="Resume session ID")
    
    # Status
    subparsers.add_parser("status", help="Статус системы")
    
    # Serve
    subparsers.add_parser("serve", help="Запустить веб-сервер")
    
    # Run-agent
    p_run = subparsers.add_parser("run-agent", help="Один запрос")
    p_run.add_argument("agent", help="ID агента")
    p_run.add_argument("--input", "-i", help="Запрос")
    
    # Test
    subparsers.add_parser("test", help="Запустить тесты")
    
    args = parser.parse_args()
    
    if not args.command:
        if check_first_run():
            return
        # Default: open TUI (like other agents)
        cmd_chat(args)
        return
    
    cmds = {
        "setup": cmd_setup,
        "chat": cmd_chat,
        "status": cmd_status,
        "serve": cmd_serve,
        "run-agent": cmd_run,
        "test": cmd_test,
    }
    
    if args.command in cmds:
        cmds[args.command](args)
    else:
        print(f"Неизвестная команда: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
