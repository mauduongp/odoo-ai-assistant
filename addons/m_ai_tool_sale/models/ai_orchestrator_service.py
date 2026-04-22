from odoo import models


class AiOrchestratorService(models.AbstractModel):
    _inherit = "m_ai.orchestrator.service"

    def _build_system_prompt(self):
        base = super()._build_system_prompt()
        return (
            base
            + " For sales questions, use model 'sale.order' with fields like "
            "'name', 'state', 'invoice_status', and 'amount_total'. "
            " For sale order creation, use action 'prepare_create_record' first with model "
            "'sale.order' and allowed values fields only. "
            "Do not call 'create_record' until the user explicitly confirms creation. "
            "When answering sales queries, prefer short natural sentences. "
            "For status questions, answer like: 'The status of SO00002 is Sales Order.' "
            "For list questions, answer with compact identifiers first, for example: "
            "'Ongoing sale orders are SO00002, SO00004.'"
        )
