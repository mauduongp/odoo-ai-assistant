from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AiChatSession(models.Model):
    _name = "m_ai.chat.session"
    _description = "AI Chat Session"
    _order = "last_message_at desc, id desc"

    name = fields.Char(required=True, default=lambda self: _("New AI Chat"))
    user_id = fields.Many2one(
        "res.users", required=True, default=lambda self: self.env.user, readonly=True
    )
    message_ids = fields.One2many(
        "m_ai.chat.message", "session_id", string="Messages", readonly=True
    )
    last_message_at = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)
    input_message = fields.Text(string="Your Message")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("user_id", self.env.user.id)
        return super().create(vals_list)

    def action_send_message(self):
        for session in self:
            if session.user_id != self.env.user:
                raise UserError(_("You can only send messages in your own session."))

            prompt = (session.input_message or "").strip()
            if not prompt:
                raise UserError(_("Please enter a message first."))

            session.env["m_ai.chat.message"].create(
                {
                    "session_id": session.id,
                    "role": "user",
                    "content": prompt,
                }
            )

            try:
                result = self.env["m_ai.chat.service"].process_message(session, prompt)
                session.env["m_ai.chat.message"].create(
                    {
                        "session_id": session.id,
                        "role": "assistant",
                        "content": result["reply"],
                        "action_name": result["action_name"],
                        "action_payload": result["action_payload"],
                    }
                )
            except Exception as exc:
                session.env["m_ai.chat.message"].create(
                    {
                        "session_id": session.id,
                        "role": "assistant",
                        "content": _("I could not process your request."),
                        "error_message": str(exc),
                    }
                )

            session.write(
                {
                    "input_message": False,
                    "last_message_at": fields.Datetime.now(),
                }
            )
