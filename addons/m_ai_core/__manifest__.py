# -*- coding: utf-8 -*-
{
    "name": "AI Core",
    "version": "1.0",
    "summary": "Core foundation for AI assistant modules",
    "sequence": 10,
    "description": """
AI Core
====================
Core provider, model, and configuration for AI modules.
    """,
    "category": "AI/AI",
    "website": "",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/ai_provider_views.xml",
        "views/ai_menu_items.xml",
        "views/res_config_setting_views.xml",
    ],
    "installable": True,
    "application": False,
    "assets": {},
    "author": "Mau DP",
    "license": "LGPL-3",
}
