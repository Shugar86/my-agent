#!/usr/bin/env python3
"""Seed workflow templates for marketplace MVP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db_manager import db
from core.db_migrate import run_migrations

TEMPLATES = [
    {
        "id": "tpl_lead_telegram_sheets",
        "name": "Новый лид → Telegram + Sheets",
        "description": "Получает webhook с новым лидом, уведомляет в Telegram и записывает в Google Sheets",
        "category": "sales",
        "tags": ["sales", "telegram", "sheets", "lead"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Summarize this lead: {{trigger.payload}}"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.telegram_chat}}", "message": "New lead: {{a1.output}}"}},
                {"id": "x2", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{config.sheet_id}}", "range": "Leads!A1", "values": ["{{trigger.payload.name}}", "{{trigger.payload.email}}"]}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}, {"from": "a1", "to": "x2"}],
        },
    },
    {
        "id": "tpl_gmail_digest_slack",
        "name": "Gmail digest → Slack",
        "description": "Ежедневная сводка непрочитанных писем в Slack",
        "category": "ops",
        "tags": ["gmail", "slack", "digest"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 9 * * *"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Create a brief email digest"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#general", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_notion_summary_email",
        "name": "Notion task → Agent summary → Email",
        "description": "Берёт задачу из Notion, генерирует summary и отправляет на email",
        "category": "productivity",
        "tags": ["notion", "email", "summary"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Summarize task: {{trigger.payload}}"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{config.email}}", "subject": "Task Summary", "body": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_telegram_support",
        "name": "Telegram Support Bot",
        "description": "Отвечает на сообщения в Telegram через AI агента",
        "category": "support",
        "tags": ["telegram", "support", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.telegram", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "{{trigger.text}}"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{trigger.chat_id}}", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_weekly_report",
        "name": "Weekly Report Generator",
        "description": "Генерирует еженедельный отчёт и отправляет в Slack",
        "category": "marketing",
        "tags": ["report", "slack", "schedule"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 10 * * 1"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "data_analyst", "prompt": "Generate weekly performance report"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#reports", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_lead_qualify",
        "name": "Lead Qualification",
        "description": "Квалифицирует лиды через AI и записывает score в Sheets",
        "category": "sales",
        "tags": ["sales", "ai", "sheets"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.new_lead", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Score this lead 1-10: {{trigger.payload}}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "a1", "field": "output", "operator": "contains", "value": "8"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.sales_chat}}", "message": "Hot lead! {{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "c1"}, {"from": "c1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_content_repurpose",
        "name": "Content Repurposing",
        "description": "Превращает blog post в social media posts",
        "category": "marketing",
        "tags": ["marketing", "content", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Create 3 social posts from: {{trigger.payload.content}}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#marketing", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_notion_daily_sync",
        "name": "Notion Daily Sync",
        "description": "Синхронизирует задачи Notion в Google Sheets",
        "category": "productivity",
        "tags": ["notion", "sheets", "sync"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 8 * * *"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "List today's tasks"}},
                {"id": "x1", "type": "action.notion_page", "config": {"parent_id": "{{config.notion_page}}", "title": "Daily Sync", "content": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_customer_feedback",
        "name": "Customer Feedback Router",
        "description": "Маршрутизирует feedback по sentiment",
        "category": "support",
        "tags": ["support", "feedback", "condition"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Analyze sentiment: {{trigger.payload.feedback}}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "a1", "operator": "contains", "value": "negative"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.support_chat}}", "message": "Urgent: {{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "c1"}, {"from": "c1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_invoice_reminder",
        "name": "Invoice Reminder",
        "description": "Напоминание об оплате через email",
        "category": "sales",
        "tags": ["sales", "email", "reminder"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 10 1 * *"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Draft invoice reminder email"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{config.client_email}}", "subject": "Invoice Reminder", "body": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_research_digest",
        "name": "Research Digest",
        "description": "Ежедневный research digest от AI researcher",
        "category": "ops",
        "tags": ["research", "schedule", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 7 * * *"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "researcher", "prompt": "Today's AI news digest"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.chat_id}}", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_webhook_to_notion",
        "name": "Webhook → Notion Database",
        "description": "Записывает webhook payload в Notion database",
        "category": "ops",
        "tags": ["webhook", "notion", "automation"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.notion_db_update", "config": {"database_id": "{{config.database_id}}", "properties": {"Name": {"title": [{"text": {"content": "{{trigger.payload.name}}"}}]}}}},
            ],
            "edges": [{"from": "t1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_sales_followup",
        "name": "Sales Follow-up Sequence",
        "description": "Auto follow-up email after lead webhook",
        "category": "sales",
        "tags": ["sales", "email", "followup"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Write follow-up for {{trigger.payload}}"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{trigger.payload.email}}", "subject": "Following up", "body": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_support_ticket",
        "name": "Support Ticket Router",
        "description": "Route support messages to Slack with AI summary",
        "category": "support",
        "tags": ["support", "slack", "routing"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.telegram", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Summarize support request: {{trigger.text}}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#support", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_marketing_campaign",
        "name": "Marketing Campaign Launcher",
        "description": "Generate campaign copy and post to Telegram",
        "category": "marketing",
        "tags": ["marketing", "telegram", "campaign"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 10 * * 1"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Weekly marketing tip"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.chat}}", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_ops_health_check",
        "name": "Ops Health Check",
        "description": "Daily health check webhook ping and Slack alert",
        "category": "ops",
        "tags": ["ops", "monitoring", "slack"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 */6 * * *"}},
                {"id": "x1", "type": "action.webhook", "config": {"url": "{{config.health_url}}", "method": "GET"}},
                {"id": "x2", "type": "action.slack", "config": {"channel": "#ops", "message": "Health check done"}},
            ],
            "edges": [{"from": "t1", "to": "x1"}, {"from": "x1", "to": "x2"}],
        },
    },
    {
        "id": "tpl_lead_scoring",
        "name": "Lead Scoring Pipeline",
        "description": "Score leads with AI and route hot leads to Telegram",
        "category": "sales",
        "tags": ["sales", "scoring", "condition"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Score lead hot or cold: {{trigger.payload}}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "a1", "field": "output", "operator": "contains", "value": "hot"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.chat}}", "message": "Hot lead: {{a1.output}}"}},
                {"id": "x2", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{config.sheet}}", "range": "Leads!A1", "values": ["cold", "{{a1.output}}"]}},
            ],
            "edges": [
                {"from": "t1", "to": "a1"}, {"from": "a1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "true"}, {"from": "c1", "to": "x2", "label": "false"},
            ],
        },
    },
    {
        "id": "tpl_content_calendar",
        "name": "Content Calendar Reminder",
        "description": "Weekly content planning reminder via email",
        "category": "marketing",
        "tags": ["marketing", "content", "schedule"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 9 * * 5"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Content ideas for next week"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{config.email}}", "subject": "Content Calendar", "body": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_customer_onboarding",
        "name": "Customer Onboarding Flow",
        "description": "Welcome new customers with personalized message",
        "category": "support",
        "tags": ["support", "onboarding", "email"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Welcome message for {{trigger.payload.name}}"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{trigger.payload.email}}", "subject": "Welcome!", "body": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_social_repurpose",
        "name": "Blog to Social Repurpose",
        "description": "Turn blog content into social posts",
        "category": "marketing",
        "tags": ["marketing", "social", "content"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Create 3 social posts from: {{trigger.payload.content}}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#marketing", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_inventory_alert",
        "name": "Inventory Low Stock Alert",
        "description": "Alert team when inventory webhook reports low stock",
        "category": "ops",
        "tags": ["ops", "inventory", "alert"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "c1", "type": "condition", "config": {"source_node": "t1", "field": "payload", "operator": "contains", "value": "low"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{config.chat}}", "message": "Low stock alert!"}},
            ],
            "edges": [{"from": "t1", "to": "c1"}, {"from": "c1", "to": "x1", "label": "true"}],
        },
    },
    {
        "id": "tpl_meeting_prep",
        "name": "Meeting Prep Assistant",
        "description": "Prepare meeting brief from calendar webhook",
        "category": "productivity",
        "tags": ["productivity", "meetings", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Meeting prep for {{trigger.payload}}"}},
                {"id": "x1", "type": "action.notion_page", "config": {"title": "Meeting Brief", "content": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_feedback_analyzer",
        "name": "Feedback Sentiment Analyzer",
        "description": "Analyze customer feedback and log to Sheets",
        "category": "support",
        "tags": ["support", "feedback", "sentiment"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Sentiment analysis: {{trigger.payload.feedback}}"}},
                {"id": "x1", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{config.sheet}}", "range": "Feedback!A1", "values": ["{{a1.output}}"]}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_competitor_monitor",
        "name": "Competitor Monitor Digest",
        "description": "Weekly competitor news digest",
        "category": "marketing",
        "tags": ["marketing", "research", "digest"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 8 * * 1"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Competitor news digest"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{config.email}}", "subject": "Competitor Digest", "body": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_hr_screening",
        "name": "HR Resume Screener",
        "description": "Screen resumes from webhook and notify HR",
        "category": "ops",
        "tags": ["ops", "hr", "recruiting"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Screen resume: {{trigger.payload}}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#hr", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
]


def seed() -> int:
    """Insert workflow templates if not present."""
    run_migrations()
    db.create_tables()
    count = 0
    for tpl in TEMPLATES:
        existing = db.fetchone("SELECT id FROM workflow_templates WHERE id = ?", (tpl["id"],))
        if existing:
            continue
        db.execute(
            """INSERT INTO workflow_templates
               (id, name, description, category, definition_json, tags_json, installs_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                tpl["id"],
                tpl["name"],
                tpl["description"],
                tpl["category"],
                json.dumps(tpl["definition"]),
                json.dumps(tpl["tags"]),
                0,
            ),
        )
        count += 1
    print(f"Seeded {count} new templates ({len(TEMPLATES)} total defined)")
    return count


if __name__ == "__main__":
    seed()
