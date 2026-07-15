# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMove(models.Model):
    _name = 'stock.move'
    _description = 'Track stock movements (in/out).'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
    )
    price = fields.Float(
        string='Price',
        required=True,
    )
    move_date = fields.Date(
        string='Move Date',
        required=True,
    )
    move_type = fields.Selection(
        selection=[['in', 'Incoming'], ['out', 'Outgoing']],
        string='Move Type',
        required=True,
    )
