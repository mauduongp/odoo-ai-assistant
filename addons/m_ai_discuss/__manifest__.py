# -*- coding: utf-8 -*-
{
    "name": "AI Discuss Assistant",
    "version": "1.0",
    "summary": "Use AI assistant directly in Odoo Discuss",
    "sequence": 30,
    "description": """
AI Discuss Assistant
====================
Bridge Discuss messages to AI core orchestrator service.
    """,
    "category": "AI/AI",
    "website": "",
    "depends": ["m_ai_core", "m_ai_tool_sale", "mail"],
    "data": [
        "data/ai_discuss_data.xml",
    ],
    "installable": True,
    "application": False,
    "assets": {},
    "author": "Mau DP",
    "license": "LGPL-3",
}
