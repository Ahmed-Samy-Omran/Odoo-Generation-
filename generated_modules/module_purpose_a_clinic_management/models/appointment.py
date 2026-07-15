# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Appointment(models.Model):
    _name = 'appointment'
    _description = 'Manages patient appointments with doctors.'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one(
        comodel_name='patient',
        string='Patient',
        required=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='doctor',
        string='Doctor',
        required=True,
    )
    appointment_date = fields.Datetime(
        string='Appointment Date',
        required=True,
    )
    price = fields.Float(
        string='Price',
    )
    state = fields.Selection(
        selection=[['draft', 'Draft'], ['confirmed', 'Confirmed'], ['cancelled', 'Cancelled']],
        string='Status',
    )
