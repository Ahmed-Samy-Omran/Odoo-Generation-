# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OfficeDocument(models.Model):
    _name = 'office.document'
    _description = 'Stores document details and attachments with status tracking.'
    _rec_name = 'name'

    name = fields.Char(
        string='Document Title',
        required=True,
    )
    doc_type = fields.Selection(
        selection=[['contract', 'Contract'], ['invoice', 'Invoice'], ['receipt', 'Receipt'], ['other', 'Other']],
        string='Document Type',
        required=True,
    )
    date = fields.Date(
        string='Date',
        required=True,
    )
    attachment = fields.Binary(
        string='File',
    )
    notes = fields.Text(
        string='Notes',
    )
    state = fields.Selection(
        selection=[['draft', 'Draft'], ['review', 'Under Review'], ['approved', 'Approved'], ['archived', 'Archived']],
        string='Status',
    )
