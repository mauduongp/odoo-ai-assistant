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
        return self._resolve_envelope(
            envelope, user_prompt=user_prompt, provider=provider
        )

    def _build_system_prompt(self):
        return (
            "You are an Odoo assistant. Return JSON only. "
            'Supported responses: {"type":"text","message":"..."} or '
            '{"type":"action","action":"query_records","arguments":{"model":"<model.name>","domain":[["name","=","VALUE"]],"fields":["name"],"limit":1}} or '
            '{"type":"action","action":"read_records","arguments":{"model":"<model.name>","ids":[1],"fields":["name"]}}. '
            "Use only allowed model names and fields."
        )

    def _resolve_envelope(self, envelope, user_prompt="", provider=None):
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
                "reply": self._format_tool_result(
                    action_name,
                    result,
                    user_prompt=user_prompt,
                    arguments=arguments,
                    provider=provider,
                ),
                "action_name": action_name,
                "action_payload": json.dumps(
                    {"arguments": arguments, "result": result}, sort_keys=True
                ),
            }

        message = envelope.get("message")
        if not message:
            message = _("I could not understand the request. Please rephrase.")
        return {"reply": message, "action_name": False, "action_payload": False}

    def _format_tool_result(
        self, action_name, result, user_prompt="", arguments=None, provider=None
    ):
        if self._is_natural_response_mode() and provider:
            answer = self._generate_natural_answer(
                provider=provider,
                user_prompt=user_prompt,
                action_name=action_name,
                arguments=arguments or {},
                result=result,
            )
            if answer:
                return answer

        count = result.get("count", 0)
        model = result.get("model", "record")
        records = result.get("records", [])
        if not records:
            return _("No %s records matched your request.") % model
        return _(
            "I found %(count)s %(model)s record(s). Raw data: %(records)s"
        ) % {
            "count": count,
            "model": model,
            "records": json.dumps(records, ensure_ascii=False),
        }

    def _is_debug_mode(self):
        value = self.env["ir.config_parameter"].sudo().get_param("m_ai.ai_debug_mode")
        return str(value).lower() in ("1", "true", "yes", "on")

    def _is_natural_response_mode(self):
        value = self.env["ir.config_parameter"].sudo().get_param(
            "m_ai.ai_natural_response_mode", "True"
        )
        return str(value).lower() in ("1", "true", "yes", "on")

    def _generate_natural_answer(
        self, provider, user_prompt, action_name, arguments, result
    ):
        generation_system_prompt = (
            "You are an Odoo assistant. Write a concise, natural answer for the user. "
            "Use only facts from the provided tool result JSON. "
            "Do not invent records, fields, or values. "
            "If no records are present, say that clearly and suggest a useful next check. "
            "Use plain sentences with no markdown bullets, no bold text, and no code blocks. "
            "Avoid repeating field names unless needed. "
            "If one record is found, answer in one sentence. "
            "If multiple records are found, summarize first and then list only key identifiers. "
            "Return plain text only. Do not return JSON."
        )
        generation_prompt = (
            f"User question:\n{user_prompt}\n\n"
            f"Action:\n{action_name}\n\n"
            f"Arguments JSON:\n{json.dumps(arguments, ensure_ascii=False)}\n\n"
            f"Tool result JSON:\n{json.dumps(result, ensure_ascii=False)}\n\n"
            "Write the final user-facing answer."
        )
        try:
            raw_answer = provider.get_response(generation_prompt, generation_system_prompt)
            return self._sanitize_final_answer(raw_answer)
        except Exception:
            _logger.exception("AI natural response generation failed")
            return False

    def _sanitize_final_answer(self, raw_answer):
        if not raw_answer:
            return False
        if isinstance(raw_answer, dict):
            if raw_answer.get("type") == "text":
                return raw_answer.get("message")
            return json.dumps(raw_answer, ensure_ascii=False)

        text = str(raw_answer).strip()
        decoder = json.JSONDecoder()
        idx = 0
        text_messages = []
        while idx < len(text):
            brace_idx = text.find("{", idx)
            if brace_idx == -1:
                break
            try:
                obj, end_idx = decoder.raw_decode(text[brace_idx:])
            except Exception:
                idx = brace_idx + 1
                continue
            if isinstance(obj, dict) and obj.get("type") == "text" and obj.get("message"):
                text_messages.append(obj.get("message"))
            idx = brace_idx + end_idx

        if text_messages:
            return text_messages[-1]
        return text
