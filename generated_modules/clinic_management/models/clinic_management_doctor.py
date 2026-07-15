# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClinicManagementDoctor(models.Model):
    _name = 'clinic_management.doctor'
    _description = 'Doctor'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    specialization = fields.Char(
        string='Specialization',
        required=True,
    )
    consultation_price = fields.Float(
        string='Consultation Price',
        required=True,
    )
    total_consultation_earnings = fields.Float(
        string='Total Consultation Earnings',
        compute='_compute_total_consultation_earnings',
    )

    @api.depends(appointment_ids.consultation_price, appointment_ids.status)
    def _compute_total_consultation_earnings(self):
        for rec in self:
            for rec in self:
                        appointments = self.env['clinic_management.appointment'].search([('doctor_id', '=', rec.id), ('status', 'in', ['confirmed', 'done'])])
                        rec.total_consultation_earnings = sum(app.consultation_price for app in appointments)

