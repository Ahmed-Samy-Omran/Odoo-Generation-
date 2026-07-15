# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClinicManagementPatient(models.Model):
    _name = 'clinic_management.patient'
    _description = 'Patient'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
        required=True,
    )
    email = fields.Char(
        string='Email',
    )
    date_of_birth = fields.Date(
        string='Date of Birth',
    )
    gender = fields.Selection(
        selection=[['male', 'Male'], ['female', 'Female'], ['other', 'Other']],
        string='Gender',
    )
    address = fields.Text(
        string='Address',
    )
