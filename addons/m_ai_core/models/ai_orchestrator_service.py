import json
import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AiOrchestratorService(models.AbstractModel):
    _name = "m_ai.orchestrator.service"
    _description = "AI Orchestrator Service"

    _ALLOWED_ACTIONS = {"query_records", "read_records"}

    def process_message(self, user_prompt):
        provider = self.env["m_ai.provider"].get_provider()
        system_prompt = self._build_system_prompt()
        envelope = provider.get_structured_response(user_prompt, system_prompt)
        if self._is_debug_mode():
            _logger.info(
                "AI debug | prompt=%s | envelope=%s",
                user_prompt,
                json.dumps(envelope, ensure_ascii=False),
            )
        return self._resolve_envelope(envelope)

    def _build_system_prompt(self):
        return (
            "You are an Odoo assistant. Return JSON only. "
            'Supported responses: {"type":"text","message":"..."} or '
            '{"type":"action","action":"query_records","arguments":{"model":"<model.name>","domain":[["name","=","VALUE"]],"fields":["name"],"limit":1}} or '
            '{"type":"action","action":"read_records","arguments":{"model":"<model.name>","ids":[1],"fields":["name"]}}. '
            "Use only allowed model names and fields."
        )

    def _resolve_envelope(self, envelope):
        response_type = envelope.get("type")
        if response_type == "action":
            action_name = envelope.get("action")
            if action_name not in self._ALLOWED_ACTIONS:
                raise UserError(_("Action '%s' is not allowed.") % (action_name or ""))
            arguments = envelope.get("arguments") or {}
            result = self.env["m_ai.tool.service"].execute_tool(action_name, arguments)
            if self._is_debug_mode():
                _logger.info(
                    "AI debug | action=%s | arguments=%s | result=%s",
                    action_name,
                    json.dumps(arguments, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False),
                )
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
        custom = self._format_model_records(model, records, count)
        if custom:
            return custom
        return _(
            "I found %(count)s %(model)s record(s). Raw data: %(records)s"
        ) % {
            "count": count,
            "model": model,
            "records": json.dumps(records, ensure_ascii=False),
        }

    def _format_model_records(self, model, records, count):
        """Return formatted human response for model, or False for default."""
        return False

    def _label_or_value(self, field_value):
        if isinstance(field_value, dict):
            return field_value.get("label") or field_value.get("value")
        return field_value

    def _is_debug_mode(self):
        value = self.env["ir.config_parameter"].sudo().get_param("m_ai.ai_debug_mode")
        return str(value).lower() in ("1", "true", "yes", "on")
