# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Patient(models.Model):
    _name = 'patient'
    _description = 'Stores patient details and medical history.'
    _rec_name = 'name'

    name = fields.Char(
        string='Patient Name',
        required=True,
    )
    phone = fields.Char(
        string='Phone Number',
        required=True,
    )
    appointment_ids = fields.One2many(
        comodel_name='appointment',
        inverse_name='patient_id',
        string='Appointments (Smart Button)',
    )
