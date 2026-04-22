import json

from odoo import _, models
from odoo.exceptions import UserError


class AiOrchestratorService(models.AbstractModel):
    _name = "m_ai.orchestrator.service"
    _description = "AI Orchestrator Service"

    _ALLOWED_ACTIONS = {"query_records", "read_records"}

    def process_message(self, user_prompt):
        provider = self.env["m_ai.provider"].get_provider()
        system_prompt = self._build_system_prompt()
        envelope = provider.get_structured_response(user_prompt, system_prompt)
        return self._resolve_envelope(envelope)

    def _build_system_prompt(self):
        return (
            "You are an Odoo assistant. Return JSON only. "
            'Supported responses: {"type":"text","message":"..."} or '
            '{"type":"action","action":"query_records","arguments":{"model":"sale.order","domain":[["name","=","SO0001"]],"fields":["name","state","invoice_status","amount_total"],"limit":1}} or '
            '{"type":"action","action":"read_records","arguments":{"model":"sale.order","ids":[1],"fields":["name","state"]}}. '
            "Prefer query_records/read_records for read-only data requests."
        )

    def _resolve_envelope(self, envelope):
        response_type = envelope.get("type")
        if response_type == "action":
            action_name = envelope.get("action")
            if action_name not in self._ALLOWED_ACTIONS:
                raise UserError(_("Action '%s' is not allowed.") % (action_name or ""))
            arguments = envelope.get("arguments") or {}
            result = self.env["m_ai.tool.service"].execute_tool(action_name, arguments)
            return {
                "reply": self._format_tool_result(action_name, result),
                "action_name": action_name,
                "action_payload": json.dumps(
                    {"arguments": arguments, "result": result}, sort_keys=True
                ),
            }

        message = envelope.get("message")
        if not message:
            message = _("I could not understand the request. Please rephrase.")
        return {"reply": message, "action_name": False, "action_payload": False}

    def _format_tool_result(self, action_name, result):
        count = result.get("count", 0)
        model = result.get("model", "record")
        records = result.get("records", [])
        if not records:
            return _("No %s records matched your request.") % model
        if model == "sale.order":
            return self._format_sale_order_records(records, count)
        return _(
            "I found %(count)s %(model)s record(s). Raw data: %(records)s"
        ) % {
            "count": count,
            "model": model,
            "records": json.dumps(records, ensure_ascii=False),
        }

    def _format_sale_order_records(self, records, count):
        lines = []
        for row in records[:5]:
            order_name = row.get("name", "Unknown")
            state = self._label_or_value(row.get("state"))
            invoice_status = self._label_or_value(row.get("invoice_status"))
            amount_total = row.get("amount_total")
            if amount_total is not None:
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
            else:
                lines.append(
                    _("%(order)s is '%(state)s', invoice status '%(invoice)s'.")
                    % {
                        "order": order_name,
                        "state": state or "n/a",
                        "invoice": invoice_status or "n/a",
                    }
                )
        prefix = _("I found %(count)s sale order(s). ") % {"count": count}
        return prefix + " ".join(lines)

    def _label_or_value(self, field_value):
        if isinstance(field_value, dict):
            return field_value.get("label") or field_value.get("value")
        return field_value
