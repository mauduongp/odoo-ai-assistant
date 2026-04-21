from odoo import fields, models


class AiChatMessage(models.Model):
    _name = "m_ai.chat.message"
    _description = "AI Chat Message"
    _order = "create_date asc, id asc"

    session_id = fields.Many2one(
        "m_ai.chat.session",
        string="Session",
        required=True,
        ondelete="cascade",
    )
    role = fields.Selection(
        [
            ("user", "User"),
            ("assistant", "Assistant"),
            ("system", "System"),
        ],
        required=True,
        default="user",
    )
    content = fields.Text(required=True)
    action_name = fields.Char(string="Action Name")
    action_payload = fields.Text(string="Action Payload")
    error_message = fields.Char(string="Error")
