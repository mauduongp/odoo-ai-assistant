from odoo import models


class AiToolService(models.AbstractModel):
    _inherit = "m_ai.tool.service"

    def _get_allowed_models(self):
        models_map = dict(super()._get_allowed_models())
        models_map["sale.order"] = {
            "id",
            "name",
            "client_order_ref",
            "state",
            "invoice_status",
            "amount_total",
            "currency_id",
            "partner_id",
            "date_order",
            "commitment_date",
            "create_date",
            "write_date",
        }
        return models_map
