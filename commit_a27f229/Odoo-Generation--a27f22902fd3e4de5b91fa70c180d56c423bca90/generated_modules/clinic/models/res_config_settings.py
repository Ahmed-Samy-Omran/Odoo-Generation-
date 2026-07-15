from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_move_sms_validation = fields.Boolean(string='Validate stock move SMS')
