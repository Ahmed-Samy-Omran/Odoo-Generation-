# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TestModuleExampleLine(models.Model):
    _name = 'test_module.example_line'
    _description = 'Example Line Model'
    _rec_name = 'name'

    name = fields.Char(
        string='Line Name',
        required=True,
    )
    example_id = fields.Many2one(
        comodel_name='test_module.example',
        string='Example',
        required=True,
    )
    quantity = fields.Integer(
        string='Quantity',
    )
    price = fields.Float(
        string='Price',
    )
