import json

from odoo import api, fields, _
from odoo.exceptions import UserError
from odoo.models import Model

class AiProvider(Model):
    _name = 'm_ai.provider'
    _description = 'AI Provider'

    name = fields.Char(compute='_compute_name')
    base_url = fields.Char(string='Base URL')
    api_key = fields.Char(string='API Key')
    provider_type = fields.Selection([], string='Provider Type')
    model_ids = fields.One2many('m_ai.model', 'provider_id', string='Models', domain=[('active', '=', True)])
    default_model_id = fields.Many2one('m_ai.model', string='Default Model')

    def _compute_name(self):
        for record in self:
            record.name = (record.provider_type or '').title()

    @api.model
    def get_provider(self, provider_type=None):
        """
        Get an AI provider instance from config parameter.
        
        :param provider_type: Optional provider type to filter by (e.g., 'openai', 'gemini')
        :return: Recordset of m_ai.provider (single record if found)
        :raises: UserError if no provider found or not configured
        """
        provider_id = self.env['ir.config_parameter'].sudo().get_param('m_ai.ai_provider_id') or 0
        if not provider_id:
            raise UserError(_("AI Provider is not set. Please set it in the Settings."))
        
        provider = self.browse(int(provider_id))
        if not provider.exists():
            raise UserError(_("AI Provider is not set. Please set it in the Settings."))
        
        if provider_type and provider.provider_type != provider_type:
            raise UserError(_("Configured AI Provider is of type '%s', but '%s' is required.") % (provider.provider_type, provider_type))
        
        return provider

    def get_response(self, prompt, system_prompt):
        """
        Abstract method to get response from AI provider
        Each provider must implement its own version of this method
        _get_response_<provider_type>
        Example:
        _get_response_openai(self, prompt, system_prompt)
        _get_response_gemini(self, prompt, system_prompt)
        _get_response_anthropic(self, prompt, system_prompt)
        """
        self.ensure_one()
        method_name = f'_get_response_{self.provider_type}'
        model_code = self.default_model_id.model_code if self.default_model_id else None
        if not hasattr(self, method_name):
            raise UserError(_("Method %s not implemented for provider %s") % (method_name, self.provider_type))
        return getattr(self, method_name)(prompt, system_prompt, model_code)

    def get_structured_response(self, prompt, system_prompt):
        self.ensure_one()
        raw_response = self.get_response(prompt, system_prompt)
        if not raw_response:
            return {"type": "text", "message": ""}
        if isinstance(raw_response, dict):
            return raw_response

        payload = raw_response.strip()
        if payload.startswith("```"):
            payload = payload.strip("`")
            payload = payload.replace("json", "", 1).strip()
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict) and parsed.get("type"):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"type": "text", "message": raw_response}

    def action_test_connection(self):
        self.ensure_one()

        try:
            res = self.get_response('HI', 'Connection Test')
            if res:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': _('Success'), 'message': _('Connection OK!'), 'type': 'success'}
                }
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))
