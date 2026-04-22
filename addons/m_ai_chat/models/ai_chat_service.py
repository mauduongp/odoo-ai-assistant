from odoo import models


class AiChatService(models.AbstractModel):
    _name = "m_ai.chat.service"
    _description = "AI Chat Service"

    def process_message(self, session, user_prompt):
        return self.env["m_ai.orchestrator.service"].process_message(user_prompt)
