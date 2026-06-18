# -*- coding: utf-8 -*-
from odoo import models, fields

class HospitalDoctor(models.Model):
    _name = 'hospital.doctor'
    _description = 'Doctor Records'    _rec_name = 'name'
name = fields.Char(        string='Doctor Name',        required=True,    )
specialty = fields.Char(        string='Specialty',    )
patient_ids = fields.One2many(        string='Patients',        comodel_name='hospital.patient',
        inverse_name='doctor_id',    )
