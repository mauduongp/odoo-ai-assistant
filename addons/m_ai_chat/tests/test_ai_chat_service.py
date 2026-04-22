# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiChatService(TransactionCase):
    def test_process_message_delegates_to_core_orchestrator(self):
        session = self.env["m_ai.chat.session"].create({"name": "S1"})
        core_result = {
            "reply": "Tool query_records returned 0 sale.order record(s): []",
            "action_name": "query_records",
            "action_payload": '{"arguments":{},"result":{}}',
        }
        service_model = self.env["m_ai.orchestrator.service"]
        with patch.object(
            type(service_model), "process_message", return_value=core_result
        ):
            result = self.env["m_ai.chat.service"].process_message(session, "status?")

        self.assertIn("query_records", result["reply"])
        self.assertEqual(result["action_name"], "query_records")
        self.assertEqual(result["action_payload"], '{"arguments":{},"result":{}}')

    def test_process_message_plain_text_fallback(self):
        session = self.env["m_ai.chat.session"].create({"name": "S2"})
        service_model = self.env["m_ai.orchestrator.service"]
        with patch.object(
            type(service_model),
            "process_message",
            return_value={"reply": "Hello from AI", "action_name": False, "action_payload": False},
        ):
            result = self.env["m_ai.chat.service"].process_message(session, "hello")
        self.assertEqual(result["reply"], "Hello from AI")
        self.assertFalse(result["action_name"])

    def test_action_send_message_creates_user_and_assistant_messages(self):
        session = self.env["m_ai.chat.session"].create(
            {"name": "S3", "input_message": "Status of order"}
        )
        service_model = self.env["m_ai.orchestrator.service"]
        with patch.object(
            type(service_model),
            "process_message",
            return_value={"reply": "AI says hello", "action_name": False, "action_payload": False},
        ):
            session.action_send_message()

        roles = session.message_ids.mapped("role")
        self.assertEqual(roles, ["user", "assistant"])
