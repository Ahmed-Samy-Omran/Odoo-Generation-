# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = 'test.new.model'
    _description = 'New Model'

    name = fields.Char(
        string='Name',
    )
