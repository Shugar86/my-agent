"""Interactive setup wizard for first-run configuration."""
import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

console = Console(force_terminal=True)

WIZARD_CONFIG_FILE = Path("data/wizard_config.json")
FIRST_RUN_MARKER = Path(".first_run_complete")

DEFAULT_PROFILES = {
    "fast": {
        "name": "Быстрый",
        "description": "NeuroAPI primary — для повседневных задач",
        "primary": "openai/gpt-5.4-nano",
        "fallback": "openrouter/owl-alpha",
        "base_url": "https://neuroapi.host/v1",
        "fallback_base_url": "https://openrouter.ai/api/v1",
    },
    "balanced": {
        "name": "Сбалансированный",
        "description": "OpenRouter primary — надёжность и качество",
        "primary": "openrouter/owl-alpha",
        "fallback": "openai/gpt-5.4-nano",
        "base_url": "https://openrouter.ai/api/v1",
        "fallback_base_url": "https://neuroapi.host/v1",
    },
    "smart": {
        "name": "Умный",
        "description": "Claude Sonnet — для сложных задач",
        "primary": "anthropic/claude-sonnet-4-20250514",
        "fallback": "openrouter/owl-alpha",
        "base_url": "https://openrouter.ai/api/v1",
        "fallback_base_url": "https://openrouter.ai/api/v1",
    },
    "local": {
        "name": "Локальный",
        "description": "Ollama на localhost — полная приватность",
        "primary": "ollama/llama3",
        "fallback": None,
        "base_url": "http://localhost:11434",
        "fallback_base_url": None,
    },
}


def is_first_run() -> bool:
    """Check if this is the first run."""
    return not FIRST_RUN_MARKER.exists()


def mark_first_run_complete():
    """Mark first run as complete."""
    FIRST_RUN_MARKER.touch()


def run_setup_wizard():
    """Run interactive first-run wizard."""
    console.print(Panel.fit(
        "[bold cyan]Добро пожаловать в My Agent![/bold cyan]\n"
        "[dim]Интерактивная настройка для первого запуска[/dim]",
        title="🚀 Setup Wizard",
        border_style="cyan",
        box=box.DOUBLE,
    ))

    # Step 1: Agent Name
    console.print("\n[bold yellow]Шаг 1:[/bold yellow] Назовите вашего агента")
    agent_name = Prompt.ask(
        "Имя агента",
        default="My Agent"
    )
    agent_id = Prompt.ask(
        "ID агента (для CLI)",
        default="myagent"
    )

    # Step 2: Choose Model Profile
    console.print("\n[bold yellow]Шаг 2:[/bold yellow] Выберите профиль модели")
    table = Table(title="Доступные профили", box=box.ROUNDED)
    table.add_column("#", style="cyan")
    table.add_column("Название", style="bold")
    table.add_column("Описание", style="dim")
    table.add_column("Primary", style="green")
    table.add_column("Fallback", style="blue")

    profiles = list(DEFAULT_PROFILES.items())
    for i, (key, p) in enumerate(profiles, 1):
        table.add_row(
            str(i),
            p["name"],
            p["description"],
            p["primary"].split("/")[-1],
            p["fallback"].split("/")[-1] if p["fallback"] else "—",
        )
    console.print(table)

    choice = Prompt.ask(
        "Выберите профиль (номер)",
        choices=[str(i) for i in range(1, len(profiles) + 1)],
        default="1",
    )
    selected_profile = profiles[int(choice) - 1]

    # Step 3: API Keys
    console.print(f"\n[bold yellow]Шаг 3:[/bold yellow] Настройка API ключей")
    console.print(f"[dim]Профиль: {selected_profile[1]['name']}[/dim]")

    api_keys = {}

    if selected_profile[0] in ("fast", "balanced", "smart"):
        neuroapi_key = Prompt.ask(
            "NeuroAPI API Key (опционально)",
            password=True,
            default="",
        )
        if neuroapi_key:
            api_keys["NEUROAPI_API_KEY"] = neuroapi_key

        openrouter_key = Prompt.ask(
            "OpenRouter API Key",
            password=True,
            default="",
        )
        if openrouter_key:
            api_keys["OPENROUTER_API_KEY"] = openrouter_key

    tavily_key = Prompt.ask(
        "Tavily API Key (для поиска, опционально)",
        password=True,
        default="",
    )
    if tavily_key:
        api_keys["TAVILY_API_KEY"] = tavily_key

    # Step 4: Skills selection
    console.print("\n[bold yellow]Шаг 4:[/bold yellow] Выберите навыки")
    all_skills = [
        ("research", "🔍 Веб-поиск и исследование"),
        ("code_analysis", "💻 Анализ и написание кода"),
        ("code_execution", "▶️ Выполнение кода (Python/JS)"),
        ("data_analyst", "📊 Анализ данных и графики"),
        ("deep_research", "🎓 Академический поиск"),
        ("docs", "📄 Генерация документов"),
        ("slides", "🎨 Создание презентаций"),
        ("email", "📧 Отправка email"),
        ("browser", "🌐 Браузерная автоматизация"),
        ("ocr", "🖼️ OCR (распознавание текста)"),
        ("image_generation", "🎨 Генерация изображений"),
        ("git_integration", "🌿 Git/GitHub"),
        ("rss_news", "📰 RSS и новости"),
        ("social_media", "📱 Twitter/X"),
        ("sql_db", "🗄️ SQL базы данных"),
        ("translation", "🌍 Перевод"),
        ("scheduler", "⏰ Планировщик задач"),
        ("vision", "👁️ Анализ изображений"),
        ("messaging", "💬 Telegram/Discord/Slack"),
        ("self_dev", "🔧 Самомодификация"),
    ]

    selected_skills = []
    for skill_id, skill_label in all_skills:
        if Confirm.ask(f"{skill_label}?", default=True):
            selected_skills.append(skill_id)

    # Step 5: Auth
    console.print("\n[bold yellow]Шаг 5:[/bold yellow] Настройка безопасности")
    admin_password = Prompt.ask(
        "Пароль администратора (мин. 12 символов)",
        password=True,
        default="",
    )
    if len(admin_password) < 12:
        console.print("[yellow]⚠️ Пароль короткий — будет использован 'admin'[/yellow]")
        admin_password = "admin"

    # Save configuration
    config = {
        "agent_name": agent_name,
        "agent_id": agent_id,
        "profile": selected_profile[0],
        "skills": selected_skills,
        "api_keys": api_keys,
        "admin_password": admin_password,
        "setup_date": datetime.now(timezone.utc).isoformat(),
    }

    # Save to .env
    env_path = Path(".env")
    env_lines = ["# My Agent — Auto-generated configuration\n"]
    for key, value in api_keys.items():
        env_lines.append(f"{key}={value}\n")
    if admin_password != "admin":
        env_lines.append(f"AGENT_PASSWORD={admin_password}\n")
    env_path.write_text("".join(env_lines), encoding="utf-8")

    # Save wizard config
    WIZARD_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    WIZARD_CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update agent.json
    profile_data = selected_profile[1]
    agent_config = {
        "model": {
            "primary": profile_data["primary"],
            "api_key": f"${{NEUROAPI_API_KEY}}" if "neuroapi" in profile_data["base_url"] else f"${{OPENROUTER_API_KEY}}",
            "base_url": profile_data["base_url"],
            "fallback": profile_data.get("fallback"),
            "fallback_api_key": f"${{OPENROUTER_API_KEY}}" if profile_data.get("fallback") and "openrouter" in str(profile_data.get("fallback_base_url", "")) else None,
            "fallback_base_url": profile_data.get("fallback_base_url"),
            "params": {"temperature": 0.7, "max_tokens": 8192},
            "max_retries": 3,
            "retry_base_delay": 5.0,
            "retry_max_delay": 60.0,
        }
    }
    Path("config/agent.json").write_text(json.dumps(agent_config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update universal agent in registry
    try:
        with open("agents/registry.json", "r", encoding="utf-8") as f:
            registry = json.load(f)
        for agent in registry.get("agents", []):
            if agent.get("id") == "universal":
                agent["skills"] = selected_skills
                agent["tools"] = _infer_tools_from_skills(selected_skills)
        with open("agents/registry.json", "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    mark_first_run_complete()

    console.print(Panel.fit(
        f"[bold green]✓ Настройка завершена![/bold green]\n\n"
        f"[cyan]Агент:[/cyan] {agent_name}\n"
        f"[cyan]Профиль:[/cyan] {profile_data['name']}\n"
        f"[cyan]Навыков:[/cyan] {len(selected_skills)}\n\n"
        f"[dim]Теперь можно запускать:[/dim]\n"
        f"  [bold]python agent.py chat[/bold]\n"
        f"  [bold]python agent.py serve[/bold]",
        title="Готово",
        border_style="green",
        box=box.DOUBLE,
    ))


def _infer_tools_from_skills(skills: list) -> list:
    """Infer tools from selected skills."""
    skill_tools = {
        "research": ["web_search", "web_scrape"],
        "code_analysis": ["file_read", "file_write"],
        "code_execution": ["execute_code"],
        "data_analyst": ["analyze_csv", "create_chart", "run_python"],
        "deep_research": ["deep_search", "scholar_search", "web_scrape"],
        "docs": ["create_document", "convert_to_format"],
        "slides": ["create_presentation", "export_pptx"],
        "email": ["send_email"],
        "browser": ["browser_navigate", "browser_click", "browser_fill", "browser_screenshot"],
        "ocr": ["ocr_image", "ocr_pdf"],
        "image_generation": ["generate_image", "generate_image_variation"],
        "git_integration": ["git_clone", "git_status", "github_list_issues", "github_create_issue"],
        "rss_news": ["parse_rss", "fetch_article"],
        "social_media": ["post_tweet", "search_tweets"],
        "sql_db": ["query_sqlite", "list_tables"],
        "translation": ["detect_language", "translate_text"],
        "scheduler": ["schedule_task", "cancel_scheduled_task", "list_scheduled_tasks"],
        "vision": ["analyze_image", "describe_screenshot"],
        "messaging": ["send_message"],
        "self_dev": ["read_source", "write_source", "run_tests", "git_commit"],
    }
    tools = set()
    for skill in skills:
        for tool in skill_tools.get(skill, []):
            tools.add(tool)
    return sorted(list(tools))


def run_reconfigure_wizard():
    """Interactive reconfiguration for different tasks."""
    console.print(Panel.fit(
        "[bold cyan]Переконфигурация агента[/bold cyan]\n"
        "[dim]Настройте под конкретную задачу[/dim]",
        title="⚙️ Configure",
        border_style="blue",
        box=box.DOUBLE,
    ))

    # Load current config
    current_skills = []
    try:
        with open("agents/registry.json", "r", encoding="utf-8") as f:
            registry = json.load(f)
        for agent in registry.get("agents", []):
            if agent.get("id") == "universal":
                current_skills = agent.get("skills", [])
                break
    except Exception:
        pass

    # Task presets
    presets = {
        "1": {
            "name": "Исследователь",
            "description": "Глубокий поиск, анализ, отчёты",
            "skills": ["research", "deep_research", "web_automation", "docs", "data_analyst"],
        },
        "2": {
            "name": "Разработчик",
            "description": "Код, ревью, Git, тестирование",
            "skills": ["code_analysis", "code_execution", "git_integration", "self_dev", "docs"],
        },
        "3": {
            "name": "Маркетолог",
            "description": "Контент, соцсети, email, аналитика",
            "skills": ["research", "rss_news", "social_media", "email", "image_generation", "slides"],
        },
        "4": {
            "name": "DevOps",
            "description": "Базы данных, API, мониторинг",
            "skills": ["sql_db", "api_integration", "git_integration", "code_execution", "scheduler"],
        },
        "5": {
            "name": "Персональный помощник",
            "description": "Перевод, email, планирование",
            "skills": ["translation", "email", "scheduler", "messaging", "ocr", "vision"],
        },
        "6": {
            "name": "Кастомный",
            "description": "Выбрать навыки вручную",
            "skills": None,
        },
    }

    console.print("\n[bold yellow]Выберите задачу:[/bold yellow]")
    for key, preset in presets.items():
        console.print(f"  [cyan]{key}.[/cyan] [bold]{preset['name']}[/bold] — {preset['description']}")

    choice = Prompt.ask("Задача", choices=list(presets.keys()), default="1")
    selected = presets[choice]

    if selected["skills"] is None:
        # Custom selection
        all_skills = [
            "research", "code_analysis", "code_execution", "data_analyst",
            "deep_research", "docs", "slides", "email", "browser",
            "ocr", "image_generation", "git_integration", "rss_news",
            "social_media", "sql_db", "translation", "scheduler",
            "vision", "messaging", "self_dev",
        ]
        selected_skills = []
        for skill in all_skills:
            if Confirm.ask(f"Включить '{skill}'?", default=skill in current_skills):
                selected_skills.append(skill)
    else:
        selected_skills = selected["skills"]

    # Update registry
    try:
        with open("agents/registry.json", "r", encoding="utf-8") as f:
            registry = json.load(f)
        for agent in registry.get("agents", []):
            if agent.get("id") == "universal":
                agent["skills"] = selected_skills
                agent["tools"] = _infer_tools_from_skills(selected_skills)
                agent["role"] = f"Ты — {selected['name']}. {selected['description']}."
                break
        with open("agents/registry.json", "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Ошибка сохранения: {e}[/red]")
        return

    console.print(Panel.fit(
        f"[bold green]✓ Агент переконфигурирован![/bold green]\n\n"
        f"[cyan]Профиль:[/cyan] {selected['name']}\n"
        f"[cyan]Навыков:[/cyan] {len(selected_skills)}\n"
        f"[cyan]Инструментов:[/cyan] {len(_infer_tools_from_skills(selected_skills))}",
        title="Готово",
        border_style="green",
        box=box.DOUBLE,
    ))
