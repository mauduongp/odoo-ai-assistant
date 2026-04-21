import json

from odoo import _, models
from odoo.exceptions import UserError


class AiChatService(models.AbstractModel):
    _name = "m_ai.chat.service"
    _description = "AI Chat Service"

    _ALLOWED_ACTIONS = {"sales_order_status"}

    def process_message(self, session, user_prompt):
        provider = self.env["m_ai.provider"].get_provider()
        system_prompt = self._build_system_prompt()
        envelope = provider.get_structured_response(user_prompt, system_prompt)
        return self._resolve_envelope(envelope, user_prompt)

    def _build_system_prompt(self):
        return (
            "You are an Odoo assistant. Return JSON only. "
            'Supported responses: {"type":"text","message":"..."} or '
            '{"type":"action","action":"sales_order_status","arguments":{"order_ref":"SO0001"}}. '
            "Use action only when order status data is needed."
        )

    def _resolve_envelope(self, envelope, user_prompt):
        response_type = envelope.get("type")
        if response_type == "action":
            action_name = envelope.get("action")
            if action_name not in self._ALLOWED_ACTIONS:
                raise UserError(_("Action '%s' is not allowed.") % (action_name or ""))
            arguments = envelope.get("arguments") or {}
            if action_name == "sales_order_status":
                result = self._get_sales_order_status(arguments)
                return {
                    "reply": self._format_sales_order_status(result),
                    "action_name": action_name,
                    "action_payload": json.dumps(
                        {"arguments": arguments, "result": result}, sort_keys=True
                    ),
                }

        message = envelope.get("message")
        if not message:
            message = _("I could not understand the request. Please rephrase.")
        return {"reply": message, "action_name": False, "action_payload": False}

    def _get_sales_order_status(self, arguments):
        order_ref = (arguments.get("order_ref") or "").strip()
        if not order_ref:
            raise UserError(_("Missing required argument: order_ref"))

        order = self.env["sale.order"].search(
            ["|", ("name", "=", order_ref), ("client_order_ref", "=", order_ref)],
            limit=1,
        )
        if not order:
            raise UserError(_("Sale order '%s' was not found.") % order_ref)

        delivery_status = getattr(order, "delivery_status", False) or getattr(
            order, "delivery_state", "n/a"
        )
        return {
            "name": order.name,
            "state": order.state,
            "customer": order.partner_id.display_name,
            "amount_total": order.amount_total,
            "currency": order.currency_id.name,
            "invoice_status": order.invoice_status,
            "delivery_status": delivery_status,
        }

    def _format_sales_order_status(self, result):
        return _(
            "Sale order %(name)s is in state '%(state)s'. Customer: %(customer)s. "
            "Total: %(amount_total)s %(currency)s. Invoice status: %(invoice_status)s. "
            "Delivery status: %(delivery_status)s."
        ) % result
