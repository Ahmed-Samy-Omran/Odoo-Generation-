# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _description = 'Lines of products in a sale order.'
    _rec_name = 'product_id'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
    )
    price_unit = fields.Float(
        string='Unit Price',
        required=True,
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price_subtotal',
    )

    @api.depends(quantity, price_unit)
    def _compute_price_subtotal(self):
        for rec in self:
            _compute_price_subtotal

