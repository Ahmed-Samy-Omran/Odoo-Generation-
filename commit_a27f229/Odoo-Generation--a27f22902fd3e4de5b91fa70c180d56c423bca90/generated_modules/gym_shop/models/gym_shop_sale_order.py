# -*- coding: utf-8 -*-
from odoo import models, fields

class GymShopSaleOrder(models.Model):
    _name = 'gym_shop.sale_order'
    _description = 'Records of product sales.'
    _rec_name = 'name'
    name = fields.Char(
        string='Order Reference',
    )
    member_id = fields.Many2one(
        comodel_name='gym_core.member',
        string='Member',
    )
    sale_date = fields.Datetime(
        string='Sale Date',
    )
    total_amount = fields.Float(
        string='Total Amount',
    )
    order_line_ids = fields.One2many(
        comodel_name='gym_shop.sale_order_line',
        inverse_name='order_id',
        string='Order Lines',
    )
