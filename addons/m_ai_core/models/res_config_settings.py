from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ai_provider_id = fields.Many2one(
        "m_ai.provider", string="AI Provider", config_parameter="m_ai.ai_provider_id"
    )
    ai_debug_mode = fields.Boolean(
        string="AI Debug Mode",
        config_parameter="m_ai.ai_debug_mode",
        help="Log tool/orchestrator internals and show detailed errors in AI chat replies.",
    )
