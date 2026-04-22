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

    def test_sale_order_human_formatter(self):
        result = self.env["m_ai.orchestrator.service"]._format_model_records(
            "sale.order",
            [
                {
                    "name": self.order.name,
                    "state": {"value": "sale", "label": "Sales Order"},
                    "invoice_status": {"value": "no", "label": "Nothing to Invoice"},
                    "amount_total": self.order.amount_total,
                }
            ],
            1,
        )
        self.assertIn("sale order", result.lower())
        self.assertIn(self.order.name, result)
