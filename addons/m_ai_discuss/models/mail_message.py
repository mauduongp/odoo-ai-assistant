import html
import re

from odoo import _, api, models


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

    def _post_ai_reply(self, channel, reply_text):
        self.ensure_one()
        bot_partner = self.env.ref(
            "m_ai_discuss.partner_ai_assistant", raise_if_not_found=False
        )
        bot_user = self.env.ref("m_ai_discuss.user_ai_assistant", raise_if_not_found=False)
        post_values = {
            "body": reply_text,
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_comment",
        }
        if bot_partner:
            post_values["author_id"] = bot_partner.id
        post_channel = channel.with_context(m_ai_skip_ai_reply=True).sudo()
        if bot_user:
            post_channel = post_channel.with_user(bot_user)
        post_channel.message_post(**post_values)

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
                result = message.env["m_ai.chat.service"].with_user(ai_user).process_message(
                    session=False, user_prompt=prompt
                )
                message._post_ai_reply(channel, result.get("reply") or _("No reply generated."))
            except Exception as exc:
                message._post_ai_reply(
                    channel, _("I could not process your request: %s") % str(exc)
                )

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        if not self.env.context.get("m_ai_skip_ai_reply"):
            messages._process_ai_assistant()
        return messages
