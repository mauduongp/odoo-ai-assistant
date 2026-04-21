# -*- coding: utf-8 -*-
{
    "name": "AI Chat Assistant",
    "version": "1.0",
    "summary": "Chat-first AI assistant for Odoo",
    "sequence": 20,
    "description": """
AI Chat Assistant
=================
Read-only AI chat assistant for Odoo workflows.
    """,
    "category": "AI/AI",
    "website": "",
    "depends": ["m_ai_base", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ai_chat_security.xml",
        "views/ai_chat_views.xml",
        "views/ai_chat_menu_items.xml",
    ],
    "installable": True,
    "application": True,
    "assets": {},
    "author": "Mau DP",
    "license": "LGPL-3",
}
