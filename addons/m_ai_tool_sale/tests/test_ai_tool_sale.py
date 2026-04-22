# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
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
        self.assertIn("prepare_create_record", prompt)

    def test_prepare_create_sale_order_returns_preview_only(self):
        start_count = self.env["sale.order"].search_count([])
        result = self.env["m_ai.tool.service"].execute_tool(
            "prepare_create_record",
            {
                "model": "sale.order",
                "values": {
                    "partner_id": self.order.partner_id.id,
                    "client_order_ref": "PO-001",
                },
            },
        )
        end_count = self.env["sale.order"].search_count([])

        self.assertTrue(result["prepared"])
        self.assertEqual(result["model"], "sale.order")
        self.assertEqual(result["values"]["partner_id"], self.order.partner_id.id)
        self.assertEqual(start_count, end_count)

    def test_create_sale_order_from_allowed_values(self):
        result = self.env["m_ai.tool.service"].execute_tool(
            "create_record",
            {
                "model": "sale.order",
                "values": {
                    "partner_id": self.order.partner_id.id,
                    "client_order_ref": "PO-002",
                },
            },
        )
        created = self.env["sale.order"].browse(result["record_id"])
        self.assertTrue(created.exists())
        self.assertEqual(created.partner_id.id, self.order.partner_id.id)
        self.assertEqual(created.client_order_ref, "PO-002")

    def test_create_sale_order_rejects_forbidden_fields(self):
        with self.assertRaises(UserError):
            self.env["m_ai.tool.service"].execute_tool(
                "create_record",
                {
                    "model": "sale.order",
                    "values": {
                        "partner_id": self.order.partner_id.id,
                        "amount_total": 999,
                    },
                },
            )
