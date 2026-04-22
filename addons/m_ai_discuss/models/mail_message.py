import json
import html
import logging
import re
import time
from urllib.parse import quote

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _extract_plain_text(self):
        self.ensure_one()
        body = self.body or ""
        body_text = html.unescape(re.sub(r"<[^>]+>", " ", body))
        body_text = re.sub(r"\s+", " ", body_text).strip()
        return body_text

    def _extract_ai_prompt(self):
        self.ensure_one()
        body_text = self._extract_plain_text()
        if not body_text:
            return False
        if not body_text.lower().startswith("/ai"):
            return False
        prompt = body_text[3:].strip()
        return prompt or False

    def _is_direct_chat_with_ai(self, channel, bot_partner):
        self.ensure_one()
        if not bot_partner:
            return False

        channel = channel.sudo()
        channel_type = getattr(channel, "channel_type", "")
        if channel_type and channel_type != "chat":
            return False

        partners = getattr(channel, "channel_partner_ids", False)
        if not partners:
            partners = getattr(channel, "partner_ids", False)
        if not partners and hasattr(channel, "channel_member_ids"):
            partners = channel.channel_member_ids.mapped("partner_id")
        partners = partners or self.env["res.partner"]
        return bot_partner in partners

    def _post_ai_reply(self, channel, reply_text, body_is_html=False):
        bot_partner = self.env.ref(
            "m_ai_discuss.partner_ai_assistant", raise_if_not_found=False
        )
        bot_user = self.env.ref("m_ai_discuss.user_ai_assistant", raise_if_not_found=False)
        post_values = {
            "body": reply_text,
            "body_is_html": body_is_html,
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_comment",
        }
        if bot_partner:
            post_values["author_id"] = bot_partner.id
        post_channel = channel.with_context(m_ai_skip_ai_reply=True).sudo()
        if bot_user:
            post_channel = post_channel.with_user(bot_user)
        for attempt in range(3):
            try:
                with self.env.cr.savepoint():
                    posted_message = post_channel.message_post(**post_values)
                return posted_message
            except Exception as exc:
                text = str(exc).lower()
                is_serialization = "could not serialize access due to concurrent update" in text
                if is_serialization and attempt < 2:
                    _logger.warning(
                        "AI discuss reply serialization retry %s/3", attempt + 1
                    )
                    time.sleep(0.15 * (attempt + 1))
                    continue
                raise
        return False

    def _get_base_url(self):
        return self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")

    def _build_pending_create_buttons_html(self, channel):
        channel_model = quote(getattr(channel, "_name", "discuss.channel"), safe="")
        channel_id = quote(str(channel.id), safe="")
        base_url = self._get_base_url().rstrip("/")
        confirm_url = (
            f"{base_url}/m_ai_discuss/confirm_create"
            f"?channel_model={channel_model}&channel_id={channel_id}"
        )
        cancel_url = (
            f"{base_url}/m_ai_discuss/cancel_create"
            f"?channel_model={channel_model}&channel_id={channel_id}"
        )
        return (
            '<p class="o_m_ai_pending_create_actions">'
            '<a href="%s" class="o_m_ai_pending_create_action o_m_ai_pending_create_action_confirm" data-action="confirm">'
            "%s</a> "
            '<a href="%s" class="o_m_ai_pending_create_action o_m_ai_pending_create_action_cancel" data-action="cancel">'
            "%s</a>"
            "</p>"
        ) % (
            confirm_url,
            _("Confirm Create"),
            cancel_url,
            _("Cancel"),
        )

    def _build_pending_create_reply_html(self, reply_text, channel):
        safe_reply = html.escape(reply_text or _("Draft prepared."))
        instruction = html.escape(
            _("No record created yet. Use the buttons below or reply with 'confirm create'.")
        )
        return (
            "<p>%s</p><p>%s</p>%s"
            % (safe_reply, instruction, self._build_pending_create_buttons_html(channel))
        )

    def _pending_create_key(self, channel, ai_user):
        channel_model = getattr(channel, "_name", "mail.channel")
        return "m_ai.pending_create.%s.%s.%s" % (
            channel_model,
            channel.id,
            ai_user.id,
        )

    def _get_pending_create(self, channel, ai_user):
        key = self._pending_create_key(channel, ai_user)
        raw = self.env["ir.config_parameter"].sudo().get_param(key)
        if not raw:
            return False
        try:
            payload = json.loads(raw)
            if payload.get("model") and isinstance(payload.get("values"), dict):
                return payload
        except Exception:
            _logger.exception("Failed to decode pending AI create payload")
        return False

    def _set_pending_create(self, channel, ai_user, payload):
        key = self._pending_create_key(channel, ai_user)
        self.env["ir.config_parameter"].sudo().set_param(
            key, json.dumps(payload, ensure_ascii=False)
        )

    def _update_pending_preview_message(self, channel, payload, done_text):
        preview_message_id = payload.get("preview_message_id")
        if not isinstance(preview_message_id, int):
            return
        preview_message = self.sudo().browse(preview_message_id).exists()
        if (
            not preview_message
            or preview_message.model != getattr(channel, "_name", "")
            or preview_message.res_id != channel.id
        ):
            return
        body = preview_message.body or ""
        replacement = '<p class="o_m_ai_pending_create_actions_done">%s</p>' % html.escape(
            done_text
        )
        updated_body = re.sub(
            r'<p class="o_m_ai_pending_create_actions">.*?</p>',
            replacement,
            body,
            flags=re.S,
            count=1,
        )
        if updated_body != body:
            preview_message.write({"body": updated_body})

    def _clear_pending_create(self, channel, ai_user):
        key = self._pending_create_key(channel, ai_user)
        self.env["ir.config_parameter"].sudo().set_param(key, "")

    def _is_confirm_prompt(self, prompt):
        text = (prompt or "").lower()
        return any(token in text for token in ("confirm", "yes, create", "create it"))

    def _is_cancel_prompt(self, prompt):
        text = (prompt or "").lower()
        return any(token in text for token in ("cancel", "stop", "do not create"))

    def _cancel_pending_create(self, channel, ai_user):
        pending_create = self._get_pending_create(channel, ai_user)
        if not pending_create:
            return False
        self._update_pending_preview_message(channel, pending_create, _("Cancelled"))
        self._clear_pending_create(channel, ai_user)
        return True

    def _confirm_pending_create(self, channel, ai_user):
        pending_create = self._get_pending_create(channel, ai_user)
        if not pending_create:
            return False
        create_result = (
            self.env["m_ai.tool.service"]
            .with_user(ai_user)
            .execute_tool("create_record", pending_create)
        )
        self._update_pending_preview_message(channel, pending_create, _("Confirmed"))
        self._clear_pending_create(channel, ai_user)
        return _(
            "Created %(model)s %(name)s (ID %(id)s)."
        ) % {
            "model": create_result.get("model", "record"),
            "name": create_result.get("record_name", ""),
            "id": create_result.get("record_id"),
        }

    def _process_ai_assistant(self):
        for message in self:
            if message.model not in ("mail.channel", "discuss.channel"):
                continue
            if message.message_type != "comment":
                continue

            bot_partner = message.env.ref(
                "m_ai_discuss.partner_ai_assistant", raise_if_not_found=False
            )
            if bot_partner and message.author_id == bot_partner:
                continue

            slash_prompt = message._extract_ai_prompt()

            channel = message.env[message.model].browse(message.res_id).exists()
            if not channel:
                continue

            is_direct_chat = message._is_direct_chat_with_ai(channel, bot_partner)
            if not slash_prompt and not is_direct_chat:
                continue
            prompt = slash_prompt or message._extract_plain_text()
            if not prompt:
                continue

            ai_user = message.author_id.user_ids[:1] or message.create_uid
            if not ai_user:
                message._post_ai_reply(
                    channel,
                    _("I can only process requests from contacts linked to an internal user."),
                )
                continue

            try:
                pending_create = message._get_pending_create(channel, ai_user)
                if pending_create and message._is_cancel_prompt(prompt):
                    message._cancel_pending_create(channel, ai_user)
                    message._post_ai_reply(channel, _("Okay, I cancelled the pending create request."))
                    continue

                if pending_create and message._is_confirm_prompt(prompt):
                    confirmation_msg = message._confirm_pending_create(channel, ai_user)
                    if confirmation_msg:
                        message._post_ai_reply(channel, confirmation_msg)
                    continue

                result = (
                    message.env["m_ai.orchestrator.service"]
                    .with_user(ai_user)
                    .process_message(prompt)
                )
                if result.get("action_name") == "prepare_create_record":
                    payload = {}
                    action_payload = result.get("action_payload") or ""
                    if action_payload:
                        try:
                            payload_wrapper = json.loads(action_payload)
                            payload = {
                                "model": (
                                    payload_wrapper.get("arguments", {}).get("model")
                                    or payload_wrapper.get("result", {}).get("model")
                                ),
                                "values": payload_wrapper.get("result", {}).get("values")
                                or payload_wrapper.get("arguments", {}).get("values")
                                or {},
                            }
                        except Exception:
                            _logger.exception("Failed to decode prepare_create_record payload")
                    if payload.get("model") and isinstance(payload.get("values"), dict):
                        reply_html = message._build_pending_create_reply_html(
                            result.get("reply"), channel
                        )
                        posted_message = message._post_ai_reply(
                            channel, reply_html, body_is_html=True
                        )
                        if posted_message and isinstance(posted_message.id, int):
                            payload["preview_message_id"] = posted_message.id
                        message._set_pending_create(channel, ai_user, payload)
                        continue
                message._post_ai_reply(channel, result.get("reply") or _("No reply generated."))
            except Exception as exc:
                _logger.exception("AI discuss processing failed")
                if message._is_ai_debug_mode():
                    msg = _("I could not process your request: %s") % str(exc)
                else:
                    msg = _(
                        "I could not process your request. Enable AI Debug Mode in Settings for detailed errors."
                    )
                message._post_ai_reply(channel, msg)

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        if not self.env.context.get("m_ai_skip_ai_reply"):
            messages._process_ai_assistant()
        return messages

    def _is_ai_debug_mode(self):
        value = self.env["ir.config_parameter"].sudo().get_param("m_ai.ai_debug_mode")
        return str(value).lower() in ("1", "true", "yes", "on")
