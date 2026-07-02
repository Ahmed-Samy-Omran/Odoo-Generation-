# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateAnOdooModulePatient(models.Model):
    _name = 'create_an_odoo_module.patient'
    _description = 'Patient'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
    )
    address = fields.Text(
        string='Address',
    )
    date_of_birth = fields.Date(
        string='Date of Birth',
    )
    gender = fields.Selection(
        selection=[['male', 'Male'], ['female', 'Female'], ['other', 'Other']],
        string='Gender',
    )
