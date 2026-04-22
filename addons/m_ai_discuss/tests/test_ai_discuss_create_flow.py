# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiDiscussCreateFlow(TransactionCase):
    def setUp(self):
        super().setUp()
        self.channel = self.env["discuss.channel"].create(
            {"name": "AI Create Channel", "channel_type": "chat"}
        )
        self.message_model = self.env["mail.message"]

    def _new_message(self, body):
        return self.message_model.with_context(m_ai_skip_ai_reply=True).create(
            {
                "body": body,
                "model": "discuss.channel",
                "res_id": self.channel.id,
                "message_type": "comment",
            }
        )

    def test_prepare_action_stores_pending_payload(self):
        message = self._new_message("/ai create draft record")
        pending_payload = {
            "arguments": {
                "model": "sale.order",
                "values": {"partner_id": self.env.user.partner_id.id},
            },
            "result": {
                "model": "sale.order",
                "values": {"partner_id": self.env.user.partner_id.id},
            },
        }
        with patch.object(
            type(self.env["m_ai.orchestrator.service"]),
            "process_message",
            return_value={
                "reply": "Preview prepared.",
                "action_name": "prepare_create_record",
                "action_payload": '{"arguments":{"model":"sale.order","values":{"partner_id":%d}},"result":{"model":"sale.order","values":{"partner_id":%d}}}'
                % (self.env.user.partner_id.id, self.env.user.partner_id.id),
            },
        ), patch.object(type(self.message_model), "_post_ai_reply"):
            message._process_ai_assistant()

        pending = message._get_pending_create(self.channel, self.env.user)
        self.assertEqual(pending["model"], pending_payload["result"]["model"])
        self.assertEqual(
            pending["values"]["partner_id"],
            pending_payload["result"]["values"]["partner_id"],
        )

    def test_prepare_reply_contains_confirm_button_link(self):
        message = self._new_message("/ai create draft record")
        with patch.object(
            type(self.env["m_ai.orchestrator.service"]),
            "process_message",
            return_value={
                "reply": "Preview prepared.",
                "action_name": "prepare_create_record",
                "action_payload": '{"arguments":{"model":"sale.order","values":{"partner_id":%d}},"result":{"model":"sale.order","values":{"partner_id":%d}}}'
                % (self.env.user.partner_id.id, self.env.user.partner_id.id),
            },
        ), patch.object(type(self.message_model), "_post_ai_reply") as mocked_post:
            message._process_ai_assistant()

        sent_body = mocked_post.call_args[0][1]
        self.assertIn("/m_ai_discuss/confirm_create", sent_body)
        self.assertIn("/m_ai_discuss/cancel_create", sent_body)

    def test_confirm_prompt_creates_record_and_clears_pending(self):
        message = self._new_message("/ai confirm create")
        message._set_pending_create(
            self.channel,
            self.env.user,
            {"model": "sale.order", "values": {"partner_id": self.env.user.partner_id.id}},
        )
        with patch.object(
            type(self.env["m_ai.tool.service"]),
            "execute_tool",
            return_value={
                "model": "sale.order",
                "record_id": 123,
                "record_name": "S000123",
                "count": 1,
                "values": {"partner_id": self.env.user.partner_id.id},
            },
        ) as mocked_execute, patch.object(type(self.message_model), "_post_ai_reply"):
            message._process_ai_assistant()

        mocked_execute.assert_called_once()
        pending = message._get_pending_create(self.channel, self.env.user)
        self.assertFalse(pending)
