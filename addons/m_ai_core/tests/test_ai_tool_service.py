# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiToolService(TransactionCase):
    def setUp(self):
        super().setUp()
        if "sale.order" not in self.env:
            self.skipTest("sale module is required for AI tool sale-order tests")
        partner = self.env["res.partner"].create({"name": "Tool Customer"})
        self.order = self.env["sale.order"].create({"partner_id": partner.id})

    def test_query_records_returns_allowed_fields(self):
        result = self.env["m_ai.tool.service"].execute_tool(
            "query_records",
            {
                "model": "sale.order",
                "domain": [("id", "=", self.order.id)],
                "fields": ["name", "state", "invoice_status", "partner_id"],
                "limit": 1,
            },
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["records"][0]["name"], self.order.name)
        self.assertIn("label", result["records"][0]["state"])

    def test_read_records_blocks_forbidden_fields(self):
        with self.assertRaises(UserError):
            self.env["m_ai.tool.service"].execute_tool(
                "read_records",
                {
                    "model": "sale.order",
                    "ids": [self.order.id],
                    "fields": ["name", "message_ids"],
                },
            )
