"""Task-based configurator for flexible agent reconfiguration."""
import json
import os
from typing import Dict, Optional

# Built-in model profiles
MODEL_PROFILES = {
    "fast": {
        "primary": "openai/gpt-5.4-nano",
        "api_key": "${NEUROAPI_API_KEY}",
        "base_url": "https://neuroapi.host/v1",
        "fallback": "openrouter/owl-alpha",
        "fallback_api_key": "${OPENROUTER_API_KEY}",
        "fallback_base_url": "https://openrouter.ai/api/v1",
        "params": {"temperature": 0.7, "max_tokens": 4096},
        "max_retries": 3,
        "retry_base_delay": 5.0,
        "retry_max_delay": 60.0,
    },
    "balanced": {
        "primary": "openrouter/owl-alpha",
        "api_key": "${OPENROUTER_API_KEY}",
        "base_url": "https://openrouter.ai/api/v1",
        "fallback": "openai/gpt-5.4-nano",
        "fallback_api_key": "${NEUROAPI_API_KEY}",
        "fallback_base_url": "https://neuroapi.host/v1",
        "params": {"temperature": 0.7, "max_tokens": 8192},
        "max_retries": 3,
        "retry_base_delay": 5.0,
        "retry_max_delay": 60.0,
    },
    "smart": {
        "primary": "anthropic/claude-sonnet-4-20250514",
        "api_key": "${OPENROUTER_API_KEY}",
        "base_url": "https://openrouter.ai/api/v1",
        "fallback": "openrouter/owl-alpha",
        "fallback_api_key": "${OPENROUTER_API_KEY}",
        "fallback_base_url": "https://openrouter.ai/api/v1",
        "params": {"temperature": 0.3, "max_tokens": 16000},
        "max_retries": 3,
        "retry_base_delay": 5.0,
        "retry_max_delay": 60.0,
    },
    "local": {
        "primary": "ollama/llama3",
        "api_key": "",
        "base_url": "http://localhost:11434",
        "params": {"temperature": 0.7, "max_tokens": 4096},
        "max_retries": 1,
        "retry_base_delay": 2.0,
        "retry_max_delay": 10.0,
    },
}

# Task presets
TASK_PRESETS: Dict[str, Dict] = {
    "researcher": {
        "name": "Исследователь",
        "description": "Глубокий поиск, анализ, отчёты",
        "skills": ["research", "deep_research", "web_automation", "docs", "data_analyst"],
        "tools": ["web_search", "web_scrape", "deep_search", "scholar_search", "create_document", "analyze_csv", "create_chart"],
        "role": "Ты — исследователь. Ты умеешь искать информацию, анализировать данные и составлять подробные отчёты.",
    },
    "developer": {
        "name": "Разработчик",
        "description": "Код, ревью, Git, тестирование",
        "skills": ["code_analysis", "code_execution", "git_integration", "self_dev", "docs"],
        "tools": ["file_read", "file_write", "execute_code", "git_clone", "git_status", "github_list_issues", "github_create_issue"],
        "role": "Ты — опытный разработчик. Ты пишешь чистый код, проводишь ревью и работаешь с Git.",
    },
    "marketer": {
        "name": "Маркетолог",
        "description": "Контент, соцсети, email, аналитика",
        "skills": ["research", "rss_news", "social_media", "email", "image_generation", "slides"],
        "tools": ["web_search", "parse_rss", "fetch_article", "post_tweet", "search_tweets", "send_email", "generate_image", "create_presentation"],
        "role": "Ты — маркетолог. Ты создаёшь контент, анализируешь тренды и управляешь соцсетями.",
    },
    "devops": {
        "name": "DevOps",
        "description": "Базы данных, API, мониторинг",
        "skills": ["sql_db", "api_integration", "git_integration", "code_execution", "scheduler"],
        "tools": ["query_sqlite", "list_tables", "api_get", "api_post", "git_clone", "execute_code", "schedule_task"],
        "role": "Ты — DevOps инженер. Ты работаешь с базами данных, API и автоматизацией.",
    },
    "assistant": {
        "name": "Персональный помощник",
        "description": "Перевод, email, планирование",
        "skills": ["translation", "email", "scheduler", "messaging", "ocr", "vision"],
        "tools": ["detect_language", "translate_text", "send_email", "schedule_task", "send_message", "ocr_image", "analyze_image"],
        "role": "Ты — личный помощник. Ты помогаешь с переводами, письмами и организацией.",
    },
    "universal": {
        "name": "Универсальный",
        "description": "Все навыки",
        "skills": [],  # Will be populated with all
        "tools": [],
        "role": "Ты — универсальный AI-ассистент с доступом ко всем инструментам.",
    },
}


def resolve_profile(profile_name: str) -> Optional[Dict]:
    """Resolve a model profile name to full configuration.
    
    Args:
        profile_name: One of 'fast', 'balanced', 'smart', 'local'
        
    Returns:
        Dict with full model configuration or None if unknown
    """
    profile = MODEL_PROFILES.get(profile_name)
    if not profile:
        return None
    
    # Resolve env vars
    resolved = {}
    for key, value in profile.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            resolved[key] = os.environ.get(env_var, "")
        else:
            resolved[key] = value
    
    return resolved


def get_task_preset(task_name: str) -> Optional[Dict]:
    """Get a task preset by name.
    
    Args:
        task_name: One of the preset names
        
    Returns:
        Dict with task configuration or None
    """
    return TASK_PRESETS.get(task_name)


def list_profiles() -> Dict[str, str]:
    """List all available model profiles.
    
    Returns:
        Dict mapping profile name to description
    """
    return {
        "fast": "NeuroAPI primary (~1.5s) — для повседневных задач",
        "balanced": "OpenRouter primary (~6s) — надёжность и качество",
        "smart": "Claude Sonnet (~8s) — для сложных задач",
        "local": "Ollama llama3 — локально, без интернета",
    }


def list_task_presets() -> Dict[str, Dict]:
    """List all available task presets.
    
    Returns:
        Dict mapping preset name to info
    """
    return {
        name: {"name": info["name"], "description": info["description"]}
        for name, info in TASK_PRESETS.items()
    }
