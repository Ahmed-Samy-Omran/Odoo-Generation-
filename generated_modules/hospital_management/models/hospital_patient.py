# -*- coding: utf-8 -*-
from odoo import models, fields

class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Patient Records'    _rec_name = 'name'
name = fields.Char(        string='Patient Name',        required=True,    )
age = fields.Integer(        string='Age',    )
gender = fields.Selection(        string='Gender',        selection=[['male', 'Male'], ['female', 'Female'], ['other', 'Other']],    )
doctor_id = fields.Many2one(        string='Primary Doctor',        comodel_name='hospital.doctor',    )
appointment_ids = fields.One2many(        string='Appointments',        comodel_name='hospital.appointment',
        inverse_name='patient_id',    )
