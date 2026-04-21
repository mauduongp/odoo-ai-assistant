# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiChatService(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Chat Customer"})
        self.order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )

    def test_process_message_sales_order_status(self):
        session = self.env["m_ai.chat.session"].create({"name": "S1"})
        envelope = {
            "type": "action",
            "action": "sales_order_status",
            "arguments": {"order_ref": self.order.name},
        }
        provider = self.env["m_ai.provider"]

        with patch.object(type(provider), "get_provider", return_value=provider), patch.object(
            type(provider), "get_structured_response", return_value=envelope
        ):
            result = self.env["m_ai.chat.service"].process_message(session, "status?")

        self.assertIn(self.order.name, result["reply"])
        self.assertEqual(result["action_name"], "sales_order_status")
        self.assertIn("arguments", result["action_payload"])

    def test_process_message_plain_text_fallback(self):
        session = self.env["m_ai.chat.session"].create({"name": "S2"})
        provider = self.env["m_ai.provider"]
        with patch.object(type(provider), "get_provider", return_value=provider), patch.object(
            type(provider),
            "get_structured_response",
            return_value={"type": "text", "message": "Hello from AI"},
        ):
            result = self.env["m_ai.chat.service"].process_message(session, "hello")
        self.assertEqual(result["reply"], "Hello from AI")
        self.assertFalse(result["action_name"])

    def test_action_send_message_creates_user_and_assistant_messages(self):
        session = self.env["m_ai.chat.session"].create(
            {"name": "S3", "input_message": "Status of order"}
        )
        provider = self.env["m_ai.provider"]
        with patch.object(type(provider), "get_provider", return_value=provider), patch.object(
            type(provider),
            "get_structured_response",
            return_value={
                "type": "action",
                "action": "sales_order_status",
                "arguments": {"order_ref": self.order.name},
            },
        ):
            session.action_send_message()

        roles = session.message_ids.mapped("role")
        self.assertEqual(roles, ["user", "assistant"])
