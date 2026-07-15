# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Doctor(models.Model):
    _name = 'doctor'
    _description = 'Stores doctor details and consultation fees.'
    _rec_name = 'name'

    name = fields.Char(
        string='Doctor Name',
        required=True,
    )
    specialty = fields.Char(
        string='Specialty',
        required=True,
    )
    consultation_fee = fields.Float(
        string='Consultation Fee',
        required=True,
    )
    total_earnings = fields.Float(
        string='Total Earnings',
        compute='_compute_total_earnings',
    )

    @api.depends(appointment_ids)
    def _compute_total_earnings(self):
        for rec in self:
            _compute_total_earnings

