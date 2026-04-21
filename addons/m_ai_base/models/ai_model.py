from odoo import fields, models, api

class AiModel(models.Model):
    _name = 'm_ai.model'
    _description = 'AI Model'

    name = fields.Char(string='Name')
    model_code = fields.Char(string='Model Code', required=True)
    provider_id = fields.Many2one('m_ai.provider', string='Provider', required=True)
    default = fields.Boolean(string='Default', default=False)
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AiModel, self).create(vals_list)
        for record in records:
            if record.default:
                record._update_default_model()
        return records

    def write(self, vals):
        res = super(AiModel, self).write(vals)
        if vals.get('default'):
            for record in self:
                record._update_default_model()
        return res

    def _update_default_model(self):
        self.ensure_one()
        if self.provider_id:
            self.search([
                ('provider_id', '=', self.provider_id.id),
                ('id', '!=', self.id)
            ]).write({'default': False})

            self.provider_id.write({
                'default_model_id': self.id
            })