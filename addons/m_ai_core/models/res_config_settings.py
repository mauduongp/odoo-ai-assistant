from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ai_provider_id = fields.Many2one(
        "m_ai.provider", string="AI Provider", config_parameter="m_ai.ai_provider_id"
    )
