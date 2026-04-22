# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiProvider(TransactionCase):
    def test_get_provider_missing_config_raises(self):
        self.env["ir.config_parameter"].sudo().set_param("m_ai.ai_provider_id", "")
        with self.assertRaises(UserError):
            self.env["m_ai.provider"].get_provider()

    def test_get_provider_invalid_id_raises(self):
        self.env["ir.config_parameter"].sudo().set_param("m_ai.ai_provider_id", "999999")
        with self.assertRaises(UserError):
            self.env["m_ai.provider"].get_provider()

    def test_get_provider_returns_configured_record(self):
        provider = self.env["m_ai.provider"].create({})
        self.env["ir.config_parameter"].sudo().set_param("m_ai.ai_provider_id", str(provider.id))
        found = self.env["m_ai.provider"].get_provider()
        self.assertEqual(found, provider)

    def test_get_provider_type_mismatch_raises(self):
        provider = self.env["m_ai.provider"].create({})
        self.env["ir.config_parameter"].sudo().set_param("m_ai.ai_provider_id", str(provider.id))
        with self.assertRaises(UserError):
            self.env["m_ai.provider"].get_provider(provider_type="openai")

    def test_get_response_requires_implementation(self):
        provider = self.env["m_ai.provider"].create({})
        with self.assertRaises(UserError):
            provider.get_response("hi", "system")

    def test_get_structured_response_json_text_fallback(self):
        provider = self.env["m_ai.provider"].create({})
        with patch.object(type(provider), "get_response", return_value='{"type":"text","message":"ok"}'):
            parsed = provider.get_structured_response("hi", "system")
            self.assertEqual(parsed.get("type"), "text")
            self.assertEqual(parsed.get("message"), "ok")

        with patch.object(type(provider), "get_response", return_value="plain response"):
            parsed = provider.get_structured_response("hi", "system")
            self.assertEqual(parsed.get("type"), "text")
            self.assertEqual(parsed.get("message"), "plain response")
