# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiToolService(TransactionCase):
    def test_query_records_blocks_unregistered_model(self):
        with self.assertRaises(UserError):
            self.env["m_ai.tool.service"].execute_tool(
                "query_records",
                {
                    "model": "res.partner",
                    "domain": [],
                    "fields": ["name"],
                },
            )

    def test_unknown_tool_rejected(self):
        with self.assertRaises(UserError):
            self.env["m_ai.tool.service"].execute_tool("delete_records", {})
