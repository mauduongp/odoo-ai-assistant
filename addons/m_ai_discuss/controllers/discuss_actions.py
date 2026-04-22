from odoo import http, _
from odoo.http import request


class AiDiscussActionsController(http.Controller):
    def _finalize_response(self, no_redirect):
        if no_redirect:
            return request.make_response("", status=204)
        return request.redirect("/web")

    @http.route(
        "/m_ai_discuss/confirm_create",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def confirm_create(self, channel_model=None, channel_id=None, **kwargs):
        no_redirect = kwargs.get("no_redirect")
        if not channel_model or not channel_id:
            return self._finalize_response(no_redirect)
        try:
            channel_id = int(channel_id)
        except Exception:
            return self._finalize_response(no_redirect)

        channel = request.env[channel_model].browse(channel_id).exists()
        if not channel:
            return self._finalize_response(no_redirect)

        mail_message = request.env["mail.message"]
        confirmation_msg = mail_message._confirm_pending_create(channel, request.env.user)
        if confirmation_msg:
            mail_message._post_ai_reply(channel, confirmation_msg)
        else:
            mail_message._post_ai_reply(
                channel, _("No pending create request found to confirm.")
            )
        return self._finalize_response(no_redirect)

    @http.route(
        "/m_ai_discuss/cancel_create",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def cancel_create(self, channel_model=None, channel_id=None, **kwargs):
        no_redirect = kwargs.get("no_redirect")
        if not channel_model or not channel_id:
            return self._finalize_response(no_redirect)
        try:
            channel_id = int(channel_id)
        except Exception:
            return self._finalize_response(no_redirect)

        channel = request.env[channel_model].browse(channel_id).exists()
        if not channel:
            return self._finalize_response(no_redirect)

        mail_message = request.env["mail.message"]
        cancelled = mail_message._cancel_pending_create(channel, request.env.user)
        if cancelled:
            mail_message._post_ai_reply(
                channel, _("Okay, I cancelled the pending create request.")
            )
        else:
            mail_message._post_ai_reply(
                channel, _("No pending create request found to cancel.")
            )
        return self._finalize_response(no_redirect)
