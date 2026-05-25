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
        "category": "hr",
        "tags": ["hr", "recruiting", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Screen resume and produce a 5-line summary: {{trigger.payload}}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#hr", "message": "{{a1.output}}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_crm_lead_enrich",
        "name": "CRM Lead Enrichment via HTTP API",
        "description": "Enrich incoming leads via external CRM API and write back to Sheets",
        "category": "sales",
        "tags": ["crm", "enrichment", "http"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "h1", "type": "action.http", "config": {
                    "url": "https://api.example.com/v1/enrich",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer {{ env(\"CRM_TOKEN\") }}"},
                    "json": {"email": "{{ trigger.payload.email }}"},
                    "retry": {"max_attempts": 3, "backoff_seconds": 2},
                }},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Score this enriched lead 1-10: {{ h1.output.body }}"}},
                {"id": "x1", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{ config.sheet }}", "range": "Leads!A1", "values": ["{{ trigger.payload.email }}", "{{ a1.output }}"]}},
            ],
            "edges": [{"from": "t1", "to": "h1"}, {"from": "h1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_crm_pipeline_digest",
        "name": "CRM Pipeline Daily Digest",
        "description": "Pull pipeline status from CRM API every morning, post digest to Slack",
        "category": "sales",
        "tags": ["crm", "digest", "schedule"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 8 * * 1-5"}},
                {"id": "h1", "type": "action.http", "config": {"url": "{{ config.crm_api }}/pipeline", "method": "GET"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "data_analyst", "prompt": "Summarize pipeline: {{ h1.output.body }}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#sales", "message": "{{ a1.output }}"}},
            ],
            "edges": [{"from": "t1", "to": "h1"}, {"from": "h1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_crm_churn_warning",
        "name": "CRM Churn Risk Alert",
        "description": "Flag accounts at churn risk based on activity webhook payload",
        "category": "sales",
        "tags": ["crm", "churn", "condition"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "data_analyst", "prompt": "Is this account at churn risk? Reply 'yes' or 'no' first. Account: {{ trigger.payload }}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "a1", "field": "output", "operator": "contains", "value": "yes"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{ config.csm_chat }}", "message": "Churn risk: {{ trigger.payload.account }} — {{ a1.output }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "a1"},
                {"from": "a1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "true"},
            ],
        },
    },
    {
        "id": "tpl_finance_invoice_capture",
        "name": "Finance: Invoice Capture from Email",
        "description": "Pull invoices from Gmail label, summarize and log to Sheets",
        "category": "finance",
        "tags": ["finance", "gmail", "sheets"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.email", "config": {"poll_interval_minutes": 15}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Extract invoice number, amount, vendor from: {{ trigger.text }}"}},
                {"id": "x1", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{ config.invoice_sheet }}", "range": "Invoices!A1", "values": ["{{ today() }}", "{{ a1.output }}"]}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_finance_expense_alert",
        "name": "Finance: Daily Expense Threshold Alert",
        "description": "Read today's expenses from Sheets, alert if over threshold",
        "category": "finance",
        "tags": ["finance", "alert", "sheets"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 18 * * *"}},
                {"id": "r1", "type": "action.sheets_read", "config": {"spreadsheet_id": "{{ config.expense_sheet }}", "range": "Today!A1:B100"}},
                {"id": "code1", "type": "util.code", "config": {"script": "rows = nodes.get('r1', {}).get('output', {}).get('values', [])\nlast_col = [float(r[1]) for r in rows[1:] if len(r) > 1 and r[1].replace('.','',1).isdigit()]\noutput = {'total': sum(last_col), 'count': len(last_col)}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "code1", "field": "total", "operator": "regex", "value": "^[5-9][0-9]{3,}|^[0-9]{5,}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#finance", "message": "Expense threshold exceeded: ${{ code1.total }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "r1"},
                {"from": "r1", "to": "code1"},
                {"from": "code1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "true"},
            ],
        },
    },
    {
        "id": "tpl_finance_invoice_followup",
        "name": "Finance: Invoice Auto Follow-up",
        "description": "Schedule overdue invoice email reminders",
        "category": "finance",
        "tags": ["finance", "email", "reminder"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 10 * * 1"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Polite payment reminder for invoice {{ trigger.payload.invoice }}"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{ config.client_email }}", "subject": "Friendly payment reminder", "body": "{{ a1.output }}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_hr_new_hire_welcome",
        "name": "HR: New Hire Welcome Pack",
        "description": "Send personalized welcome email + Slack ping when new hire webhook fires",
        "category": "hr",
        "tags": ["hr", "onboarding", "welcome"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "set1", "type": "util.set", "config": {"values": {"name": "{{ trigger.payload.name }}", "role": "{{ trigger.payload.role }}"}}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Write a 4-paragraph welcome message for {{ set1.name }}, role {{ set1.role }}"}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "Welcome to the team, {{ set1.name }}!", "body": "{{ a1.output }}"}},
                {"id": "x2", "type": "action.slack", "config": {"channel": "#general", "message": "Please welcome {{ set1.name }} ({{ set1.role }})!"}},
            ],
            "edges": [
                {"from": "t1", "to": "set1"},
                {"from": "set1", "to": "a1"},
                {"from": "a1", "to": "x1"},
                {"from": "set1", "to": "x2"},
            ],
        },
    },
    {
        "id": "tpl_hr_pto_request",
        "name": "HR: PTO Request Routing",
        "description": "Route PTO webhook through approval Slack and confirm via email",
        "category": "hr",
        "tags": ["hr", "approval", "slack"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#hr-approvals", "message": "PTO request: {{ trigger.payload.name }} {{ trigger.payload.start }} → {{ trigger.payload.end }}"}},
                {"id": "x2", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "PTO request received", "body": "Your PTO request was logged. We'll respond within 24h."}},
            ],
            "edges": [{"from": "t1", "to": "x1"}, {"from": "t1", "to": "x2"}],
        },
    },
    {
        "id": "tpl_hr_quarterly_review",
        "name": "HR: Quarterly Review Reminder",
        "description": "Quarterly review reminders for managers via email + Notion checklist",
        "category": "hr",
        "tags": ["hr", "review", "schedule"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 10 1 */3 *"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Generate a 5-point quarterly review checklist."}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{ config.managers_email }}", "subject": "Quarterly review prep", "body": "{{ a1.output }}"}},
                {"id": "x2", "type": "action.notion_page", "config": {"parent_id": "{{ config.notion_root }}", "title": "Q-Review Checklist {{ today() }}", "content": "{{ a1.output }}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}, {"from": "a1", "to": "x2"}],
        },
    },
    {
        "id": "tpl_data_etl_http",
        "name": "Data: HTTP → Transform → Sheets ETL",
        "description": "Scheduled HTTP ETL with Python transform into Google Sheets",
        "category": "ops",
        "tags": ["etl", "http", "code"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 */1 * * *"}},
                {"id": "h1", "type": "action.http", "config": {"url": "{{ config.api_url }}", "method": "GET", "retry": {"max_attempts": 3, "backoff_seconds": 5}}},
                {"id": "code1", "type": "util.code", "config": {"script": "items = nodes.get('h1', {}).get('output', {}).get('body', [])\nrows = [[i.get('id'), i.get('value', 0)] for i in items if isinstance(i, dict)]\noutput = {'rows': rows, 'count': len(rows)}"}},
                {"id": "x1", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{ config.sheet }}", "range": "ETL!A2", "values": "{{ code1.rows }}"}},
            ],
            "edges": [{"from": "t1", "to": "h1"}, {"from": "h1", "to": "code1"}, {"from": "code1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_alert_with_error_route",
        "name": "Resilient Alert with Error Fallback",
        "description": "Primary Slack alert, fallback to Telegram if Slack fails",
        "category": "ops",
        "tags": ["resilience", "error", "alert"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#alerts", "message": "Alert: {{ trigger.payload.message }}", "retry": {"max_attempts": 2, "backoff_seconds": 1}, "continue_on_error": True}},
                {"id": "x2", "type": "action.telegram", "config": {"chat_id": "{{ config.fallback_chat }}", "message": "Slack failed. Original: {{ trigger.payload.message }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "x1"},
                {"from": "x1", "to": "x2", "label": "error"},
            ],
        },
    },
    {
        "id": "tpl_status_page_monitor",
        "name": "Status Page Monitor (HTTP + Conditional Alert)",
        "description": "Ping a status URL hourly; alert when not 'ok'",
        "category": "ops",
        "tags": ["monitoring", "http", "alert"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 * * * *"}},
                {"id": "h1", "type": "action.http", "config": {"url": "{{ config.status_url }}", "method": "GET"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "h1", "field": "body", "operator": "contains", "value": "ok"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{ config.ops_chat }}", "message": "Service degraded: {{ h1.output.body }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "h1"},
                {"from": "h1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "false"},
            ],
        },
    },
    {
        "id": "tpl_marketing_ab_winner",
        "name": "Marketing: Auto-pick A/B winner",
        "description": "Read A/B variant metrics from Sheets, declare winner, post to Slack",
        "category": "marketing",
        "tags": ["marketing", "ab-test", "code"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 9 * * 5"}},
                {"id": "r1", "type": "action.sheets_read", "config": {"spreadsheet_id": "{{ config.ab_sheet }}", "range": "AB!A1:C10"}},
                {"id": "code1", "type": "util.code", "config": {"script": "vals = nodes.get('r1', {}).get('output', {}).get('values', [])[1:]\npairs = [(r[0], float(r[2])) for r in vals if len(r) > 2 and r[2].replace('.','',1).isdigit()]\nwinner = max(pairs, key=lambda p: p[1]) if pairs else ('none', 0)\noutput = {'winner': winner[0], 'rate': winner[1]}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#growth", "message": "A/B winner: {{ code1.winner }} ({{ code1.rate }}%)"}},
            ],
            "edges": [{"from": "t1", "to": "r1"}, {"from": "r1", "to": "code1"}, {"from": "code1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_marketing_drip",
        "name": "Marketing: 3-step Drip Campaign",
        "description": "Send 3 staged emails with wait nodes between them",
        "category": "marketing",
        "tags": ["marketing", "drip", "wait"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "Welcome", "body": "Day 1 message"}},
                {"id": "w1", "type": "util.wait", "config": {"seconds": 30}},
                {"id": "x2", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "Day 2", "body": "Day 2 message"}},
                {"id": "w2", "type": "util.wait", "config": {"seconds": 30}},
                {"id": "x3", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "Day 3", "body": "Day 3 message"}},
            ],
            "edges": [
                {"from": "t1", "to": "x1"}, {"from": "x1", "to": "w1"},
                {"from": "w1", "to": "x2"}, {"from": "x2", "to": "w2"},
                {"from": "w2", "to": "x3"},
            ],
        },
    },
    {
        "id": "tpl_support_priority_router",
        "name": "Support: Priority Router (3-way)",
        "description": "Classify incoming ticket as urgent/normal/low and route accordingly",
        "category": "support",
        "tags": ["support", "routing", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Classify priority (urgent/normal/low) for: {{ trigger.payload.message }}. First word is the answer."}},
                {"id": "c1", "type": "condition", "config": {"source_node": "a1", "field": "output", "operator": "contains", "value": "urgent"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{ config.urgent_chat }}", "message": "URGENT: {{ trigger.payload.message }}"}},
                {"id": "x2", "type": "action.slack", "config": {"channel": "#support", "message": "Ticket: {{ trigger.payload.message }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "a1"},
                {"from": "a1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "true"},
                {"from": "c1", "to": "x2", "label": "false"},
            ],
        },
    },
    {
        "id": "tpl_finance_payment_received",
        "name": "Finance: Payment Received Notification",
        "description": "Webhook from payment provider — log to Sheets and notify team",
        "category": "finance",
        "tags": ["finance", "payment", "webhook"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "set1", "type": "util.set", "config": {"values": {"amount": "{{ trigger.payload.amount }}", "customer": "{{ trigger.payload.customer }}", "ts": "{{ now() }}"}}},
                {"id": "x1", "type": "action.sheets_write", "config": {"spreadsheet_id": "{{ config.payments_sheet }}", "range": "Payments!A1", "values": ["{{ set1.ts }}", "{{ set1.customer }}", "{{ set1.amount }}"]}},
                {"id": "x2", "type": "action.slack", "config": {"channel": "#payments", "message": "💸 {{ set1.customer }} paid ${{ set1.amount }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "set1"},
                {"from": "set1", "to": "x1"},
                {"from": "set1", "to": "x2"},
            ],
        },
    },
    {
        "id": "tpl_growth_signup_welcome",
        "name": "Growth: Signup Welcome + CRM Sync",
        "description": "On signup webhook, welcome user and POST to CRM",
        "category": "sales",
        "tags": ["signup", "crm", "welcome"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "Welcome aboard", "body": "Hi {{ trigger.payload.name }}, thanks for signing up!"}},
                {"id": "h1", "type": "action.http", "config": {"url": "{{ config.crm_sync_url }}", "method": "POST", "json": {"email": "{{ trigger.payload.email }}", "source": "signup"}}},
            ],
            "edges": [{"from": "t1", "to": "x1"}, {"from": "t1", "to": "h1"}],
        },
    },
    {
        "id": "tpl_ops_log_ingest",
        "name": "Ops: Log Webhook → Notion DB",
        "description": "Persist incident logs into Notion database via webhook",
        "category": "ops",
        "tags": ["ops", "notion", "logs"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.notion_db_update", "config": {
                    "database_id": "{{ config.notion_db }}",
                    "properties": {"Title": {"title": [{"text": {"content": "{{ trigger.payload.title }}"}}]}, "Severity": {"select": {"name": "{{ trigger.payload.severity }}"}}}
                }},
            ],
            "edges": [{"from": "t1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_productivity_daily_standup",
        "name": "Productivity: Daily Standup Composer",
        "description": "Pull yesterday's tasks from Notion, compose standup, post to Slack",
        "category": "productivity",
        "tags": ["productivity", "standup", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "30 9 * * 1-5"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Write a 3-line standup update for yesterday's progress."}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#standup", "message": "Daily standup:\n{{ a1.output }}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_security_failed_login",
        "name": "Security: Failed Login Threshold",
        "description": "Alert via Telegram when failed-login count crosses threshold",
        "category": "ops",
        "tags": ["security", "alert", "code"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "code1", "type": "util.code", "config": {"script": "count = int(trigger.get('count', 0))\noutput = {'critical': count >= 5, 'count': count}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "code1", "field": "critical", "operator": "contains", "value": "True"}},
                {"id": "x1", "type": "action.telegram", "config": {"chat_id": "{{ config.security_chat }}", "message": "Brute-force alert: {{ code1.count }} failed logins"}},
            ],
            "edges": [
                {"from": "t1", "to": "code1"},
                {"from": "code1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "true"},
            ],
        },
    },
    {
        "id": "tpl_sales_quote_generation",
        "name": "Sales: Auto Quote Generation",
        "description": "From product webhook, generate quote PDF brief and email it",
        "category": "sales",
        "tags": ["sales", "quote", "ai"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Draft a quote for {{ trigger.payload.product }}, qty {{ trigger.payload.qty }}."}},
                {"id": "x1", "type": "action.gmail_send", "config": {"to": "{{ trigger.payload.email }}", "subject": "Your quote", "body": "{{ a1.output }}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_support_kb_assistant",
        "name": "Support: KB-grounded Reply Drafter",
        "description": "Combine HTTP KB lookup with AI reply, send to support channel",
        "category": "support",
        "tags": ["support", "kb", "http"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "h1", "type": "action.http", "config": {"url": "{{ config.kb_search_url }}?q={{ trigger.payload.question }}", "method": "GET"}},
                {"id": "merge", "type": "util.merge", "config": {"sources": ["t1", "h1"], "strategy": "shallow"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "universal", "prompt": "Use this KB context: {{ h1.output.body }}\nAnswer: {{ trigger.payload.question }}"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#support", "message": "Draft reply: {{ a1.output }}"}},
            ],
            "edges": [
                {"from": "t1", "to": "h1"},
                {"from": "h1", "to": "merge"},
                {"from": "merge", "to": "a1"},
                {"from": "a1", "to": "x1"},
            ],
        },
    },
    {
        "id": "tpl_marketing_seo_brief",
        "name": "Marketing: SEO Brief Generator",
        "description": "Weekly SEO topic ideas via AI, posted to Notion",
        "category": "marketing",
        "tags": ["seo", "content", "notion"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 9 * * 1"}},
                {"id": "a1", "type": "agent.skill", "config": {"agent_id": "marketer", "prompt": "Suggest 5 SEO topic briefs for our SaaS audience."}},
                {"id": "x1", "type": "action.notion_page", "config": {"parent_id": "{{ config.seo_page }}", "title": "SEO Briefs {{ today() }}", "content": "{{ a1.output }}"}},
            ],
            "edges": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "x1"}],
        },
    },
    {
        "id": "tpl_ops_data_quality_check",
        "name": "Ops: Data Quality Check + Retry",
        "description": "Pull dataset via HTTP with retries, run quality script, alert if bad",
        "category": "ops",
        "tags": ["data", "quality", "retry"],
        "definition": {
            "nodes": [
                {"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 6 * * *"}},
                {"id": "h1", "type": "action.http", "config": {"url": "{{ config.dataset_url }}", "method": "GET", "retry": {"max_attempts": 4, "backoff_seconds": 3}}},
                {"id": "code1", "type": "util.code", "config": {"script": "rows = nodes.get('h1', {}).get('output', {}).get('body', [])\nbad = [r for r in rows if not isinstance(r, dict) or not r.get('id')]\noutput = {'bad_count': len(bad), 'total': len(rows), 'ratio': (len(bad) / max(1, len(rows)))}"}},
                {"id": "c1", "type": "condition", "config": {"source_node": "code1", "field": "ratio", "operator": "regex", "value": "^0\\.[1-9]"}},
                {"id": "x1", "type": "action.slack", "config": {"channel": "#data-quality", "message": "Quality regression: {{ code1.bad_count }}/{{ code1.total }} bad rows"}},
            ],
            "edges": [
                {"from": "t1", "to": "h1"},
                {"from": "h1", "to": "code1"},
                {"from": "code1", "to": "c1"},
                {"from": "c1", "to": "x1", "label": "true"},
            ],
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
