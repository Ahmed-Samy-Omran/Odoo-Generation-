# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateASimpleHospitalDoctor(models.Model):
    _name = 'create_a_simple_hospital.doctor'
    _description = 'Doctor'
    _rec_name = 'name'

    name = fields.Char(
        string='Full Name',
        required=True,
    )
    specialty = fields.Char(
        string='Specialty',
    )
    phone = fields.Char(
        string='Phone Number',
    )
