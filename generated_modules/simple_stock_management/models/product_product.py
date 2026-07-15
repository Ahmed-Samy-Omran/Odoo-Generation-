# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductProduct(models.Model):
    _name = 'product.product'
    _description = 'Manage products in stock.'
    _rec_name = 'name'

    name = fields.Char(
        string='Product Name',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        compute='_compute_quantity',
    )

    @api.depends(stock_move_ids)
    def _compute_quantity(self):
        for rec in self:
            _compute_quantity

    price = fields.Float(
        string='Price',
        required=True,
    )
    stock_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='product_id',
        string='Stock Moves',
    )
