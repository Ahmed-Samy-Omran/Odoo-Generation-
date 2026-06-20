# -*- coding: utf-8 -*-
from odoo import models, fields

class GymShopSaleOrderLine(models.Model):
    _name = 'gym_shop.sale_order_line'
    _description = 'Individual items in a sale order.'
    order_id = fields.Many2one(
        comodel_name='gym_shop.sale_order',
        string='Sale Order',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='gym_shop.product',
        string='Product',
        required=True,
    )
    quantity = fields.Integer(
        string='Quantity',
    )
    unit_price = fields.Float(
        string='Unit Price',
    )
    subtotal = fields.Float(
        string='Subtotal',
    )
