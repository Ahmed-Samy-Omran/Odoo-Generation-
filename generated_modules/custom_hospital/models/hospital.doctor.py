# -*- coding: utf-8 -*-
from odoo import models, fields

class Hospital.doctor(models.Model):
    _name = 'custom_hospital.hospital.doctor'
    _description = 'Doctor Records'    _rec_name = 'name'
name = fields.Char(        string='None',        required=True,    )
specialty = fields.Char(        string='None',    )
