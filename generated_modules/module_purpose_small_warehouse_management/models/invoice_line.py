# -*- coding: utf-8 -*-
from odoo import models, fields, api

class InvoiceLine(models.Model):
    _name = 'invoice.line'
    _description = 'Handles individual line items within an invoice.'
    _rec_name = 'product_id'

    invoice_id = fields.Many2one(
        comodel_name='invoice',
        string='Invoice',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product',
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

    def _compute_price_subtotal(self):
        for rec in self:
            _compute_price_subtotal

