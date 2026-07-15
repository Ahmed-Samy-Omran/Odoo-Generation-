# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateASimpleHospitalAppointment(models.Model):
    _name = 'create_a_simple_hospital.appointment'
    _description = 'Appointment'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one(
        comodel_name='create_a_simple_hospital.patient',
        string='Patient',
        required=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='create_a_simple_hospital.doctor',
        string='Doctor',
        required=True,
    )
    appointment_datetime = fields.Datetime(
        string='Appointment Date and Time',
        required=True,
    )
    state = fields.Selection(
        selection=[['scheduled', 'Scheduled'], ['completed', 'Completed'], ['canceled', 'Canceled']],
        string='Status',
    )
