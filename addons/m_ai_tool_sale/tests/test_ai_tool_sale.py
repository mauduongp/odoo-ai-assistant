# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiToolSale(TransactionCase):
    def setUp(self):
        super().setUp()
        partner = self.env["res.partner"].create({"name": "Sale Tool Customer"})
        self.order = self.env["sale.order"].create({"partner_id": partner.id})

    def test_sale_order_allowed_for_query_records(self):
        result = self.env["m_ai.tool.service"].execute_tool(
            "query_records",
            {
                "model": "sale.order",
                "domain": [("id", "=", self.order.id)],
                "fields": ["name", "state", "invoice_status", "amount_total"],
                "limit": 1,
            },
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["records"][0]["name"], self.order.name)

    def test_sale_prompt_hint_added(self):
        prompt = self.env["m_ai.orchestrator.service"]._build_system_prompt()
        self.assertIn("sale.order", prompt)
        self.assertIn("invoice_status", prompt)
