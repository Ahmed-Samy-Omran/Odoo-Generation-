# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _name = 'sale.order'
    _description = 'Sales orders management.'
    _rec_name = 'reference'

    reference = fields.Char(
        string='Invoice Number',
        required=True,
    )
    date = fields.Datetime(
        string='Date',
        required=True,
    )
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
    )
    order_line_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='None',
        string='Order Lines',
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
    )

    @api.depends(order_line_ids, discount, tax)
    def _compute_total_amount(self):
        for rec in self:
            _compute_total_amount

    state = fields.Selection(
        selection=[['draft', 'Draft'], ['confirmed', 'Confirmed'], ['paid', 'Paid'], ['cancelled', 'Cancelled']],
        string='Status',
    )
    discount = fields.Float(
        string='Discount (%)',
    )
    tax = fields.Float(
        string='Tax (%)',
    )
