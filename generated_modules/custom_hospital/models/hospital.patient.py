# -*- coding: utf-8 -*-
from odoo import models, fields

class Hospital.patient(models.Model):
    _name = 'custom_hospital.hospital.patient'
    _description = 'Patient Records'    _rec_name = 'name'
name = fields.Char(        string='None',        required=True,    )
age = fields.Integer(        string='None',    )
gender = fields.Selection(        string='None',    )
doctor_id = fields.Many2one(        string='None',        comodel_name='hospital.doctor',    )
