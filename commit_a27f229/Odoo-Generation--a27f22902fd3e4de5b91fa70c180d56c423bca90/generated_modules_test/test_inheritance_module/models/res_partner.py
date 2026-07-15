# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Customized Partner'

    x_custom_field = fields.Char(
        string='Custom Field',
    )
