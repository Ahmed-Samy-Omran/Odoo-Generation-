# -*- coding: utf-8 -*-
from odoo import models, fields

class HospitalModulePatient(models.Model):
    _name = 'hospital_module.patient'
    _description = 'Patient Records'    _rec_name = 'name'
name = fields.Char(        string='Patient Name',        required=True,    )
age = fields.Integer(        string='Age',    )
doctor_id = fields.Many2one(        string='Primary Doctor',        comodel_name='hospital_module.doctor',    )
