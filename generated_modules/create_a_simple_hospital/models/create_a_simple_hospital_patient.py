# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateASimpleHospitalPatient(models.Model):
    _name = 'create_a_simple_hospital.patient'
    _description = 'Patient'
    _rec_name = 'name'

    name = fields.Char(
        string='Full Name',
        required=True,
    )
    date_of_birth = fields.Date(
        string='Date of Birth',
    )
    gender = fields.Selection(
        selection=[['male', 'Male'], ['female', 'Female'], ['other', 'Other']],
        string='Gender',
    )
    phone = fields.Char(
        string='Phone Number',
    )
    address = fields.Text(
        string='Address',
    )
