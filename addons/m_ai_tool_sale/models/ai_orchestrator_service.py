from odoo import _, models


class AiOrchestratorService(models.AbstractModel):
    _inherit = "m_ai.orchestrator.service"

    def _build_system_prompt(self):
        base = super()._build_system_prompt()
        return (
            base
            + " For sales questions, use model 'sale.order' with fields like "
            "'name', 'state', 'invoice_status', and 'amount_total'."
        )

    def _format_model_records(self, model, records, count):
        if model != "sale.order":
            return super()._format_model_records(model, records, count)

        lines = []
        for row in records[:5]:
            order_name = row.get("name")
            if not order_name:
                order_id = row.get("id")
                order_name = f"Sale order #{order_id}" if order_id else "Sale order"
            state = self._label_or_value(row.get("state"))
            invoice_status = self._label_or_value(row.get("invoice_status"))
            amount_total = row.get("amount_total")
            if amount_total is not None and invoice_status:
                lines.append(
                    _(
                        "%(order)s is '%(state)s', invoice status '%(invoice)s', total %(amount)s."
                    )
                    % {
                        "order": order_name,
                        "state": state or "n/a",
                        "invoice": invoice_status or "n/a",
                        "amount": amount_total,
                    }
                )
            elif amount_total is not None:
                lines.append(
                    _("%(order)s is '%(state)s', total %(amount)s.")
                    % {
                        "order": order_name,
                        "state": state or "n/a",
                        "amount": amount_total,
                    }
                )
            elif invoice_status:
                lines.append(
                    _("%(order)s is '%(state)s', invoice status '%(invoice)s'.")
                    % {
                        "order": order_name,
                        "state": state or "n/a",
                        "invoice": invoice_status,
                    }
                )
            else:
                lines.append(
                    _("%(order)s is '%(state)s'.")
                    % {
                        "order": order_name,
                        "state": state or "n/a",
                    }
                )
        prefix = _("I found %(count)s sale order(s). ") % {"count": count}
        return prefix + " ".join(lines)
