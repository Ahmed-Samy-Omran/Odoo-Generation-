# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateAnOdooModuleAppointment(models.Model):
    _name = 'create_an_odoo_module.appointment'
    _description = 'Appointment'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one(
        comodel_name='create_an_odoo_module.patient',
        string='Patient',
        required=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='create_an_odoo_module.doctor',
        string='Doctor',
        required=True,
    )
    appointment_datetime = fields.Datetime(
        string='Appointment Date & Time',
        required=True,
    )
    status = fields.Selection(
        selection=[['draft', 'Draft'], ['confirmed', 'Confirmed'], ['cancelled', 'Cancelled'], ['completed', 'Completed']],
        string='Status',
    )
