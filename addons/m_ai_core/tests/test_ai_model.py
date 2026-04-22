# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAiModel(TransactionCase):
    def test_create_with_default_sets_provider_default_model(self):
        provider = self.env["m_ai.provider"].create({})
        model = self.env["m_ai.model"].create(
            {
                "name": "Test model",
                "model_code": "test-code",
                "provider_id": provider.id,
                "default": True,
            }
        )
        self.assertEqual(provider.default_model_id, model)

    def test_second_default_clears_previous(self):
        provider = self.env["m_ai.provider"].create({})
        m1 = self.env["m_ai.model"].create(
            {
                "name": "M1",
                "model_code": "m1",
                "provider_id": provider.id,
                "default": True,
            }
        )
        m2 = self.env["m_ai.model"].create(
            {
                "name": "M2",
                "model_code": "m2",
                "provider_id": provider.id,
                "default": True,
            }
        )
        m1.invalidate_recordset()
        self.assertFalse(m1.default)
        self.assertTrue(m2.default)
        self.assertEqual(provider.default_model_id, m2)
