# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Invoice(models.Model):
    _name = 'invoice'
    _description = 'Handles purchase/sales invoices related to products.'
    _rec_name = 'name'

    name = fields.Char(
        string='Invoice Number',
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier/Customer',
        required=True,
    )
    date_invoice = fields.Date(
        string='Invoice Date',
        required=True,
    )
    state = fields.Selection(
        selection=[['draft', 'Draft'], ['open', 'Open'], ['paid', 'Paid'], ['cancel', 'Cancelled']],
        string='Status',
    )
    payment_method = fields.Selection(
        selection=[['cash', 'Cash'], ['bank_transfer', 'Bank Transfer'], ['credit_card', 'Credit Card']],
        string='Payment Method',
    )
    invoice_line_ids = fields.One2many(
        comodel_name='invoice.line',
        inverse_name='None',
        string='Invoice Lines',
    )
    amount_total = fields.Float(
        string='Total Amount',
        compute='_compute_amount_total',
    )

    def _compute_amount_total(self):
        for rec in self:
            _compute_amount_total

