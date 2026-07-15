# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'
    _description = 'Customer information (extended from base model).'

    phone = fields.Char(
        string='Phone',
    )
    street = fields.Char(
        string='Street',
    )
    city = fields.Char(
        string='City',
    )
