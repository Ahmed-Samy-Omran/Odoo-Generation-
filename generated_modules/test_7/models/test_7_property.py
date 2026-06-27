# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Test7Property(models.Model):
    _name = 'test_7.property'
    _description = 'Property'
    _rec_name = 'name'

    name = fields.Char(
        string='Property Name',
        required=True,
    )
    price = fields.Float(
        string='Price',
        required=True,
    )
    status = fields.Selection(
        selection=[['available', 'Available'], ['sold', 'Sold'], ['reserved', 'Reserved']],
        string='Status',
        required=True,
    )
