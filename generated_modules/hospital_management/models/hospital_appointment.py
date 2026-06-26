# -*- coding: utf-8 -*-
from odoo import models, fields


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Patient Appointments'
    _rec_name = 'name'


name = fields.Char(string='Appointment Ref', required=True, )
patient_id = fields.Many2one(string='Patient', required=True, comodel_name='hospital.patient', )
doctor_id = fields.Many2one(string='Doctor', required=True, comodel_name='hospital.doctor', )
appointment_date = fields.Datetime(string='Appointment Date', )
