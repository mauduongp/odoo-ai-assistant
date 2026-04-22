# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'OpenAI Provider',
    'version': '1.0',
    'summary': 'OpenAI Provider',
    'sequence': 10,
    'description': """
OpenAI Provider
====================
    """,
    'category': 'AI/AI',
    'website': '',
    'depends': ['m_ai_core'],
    'data': [
        'data/model_data.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
    },
    'author': 'Mau DP',
    'license': 'LGPL-3',
}
