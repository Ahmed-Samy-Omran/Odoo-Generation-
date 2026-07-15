# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClinicManagementAppointment(models.Model):
    _name = 'clinic_management.appointment'
    _description = 'Appointment'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one(
        comodel_name='clinic_management.patient',
        string='Patient',
        required=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='clinic_management.doctor',
        string='Doctor',
        required=True,
    )
    appointment_datetime = fields.Datetime(
        string='Appointment Date & Time',
        required=True,
    )
    status = fields.Selection(
        selection=[['draft', 'Draft'], ['confirmed', 'Confirmed'], ['done', 'Done'], ['canceled', 'Canceled'], ['no_show', 'No-Show']],
        string='Status',
    )
    consultation_price = fields.Float(
        string='Consultation Price',
        compute='_compute_consultation_price',
    )

    @api.depends(doctor_id)
    def _compute_consultation_price(self):
        for rec in self:
            for rec in self:
                        if rec.doctor_id:
                            rec.consultation_price = rec.doctor_id.consultation_price
                        else:
                            rec.consultation_price = 0.0

