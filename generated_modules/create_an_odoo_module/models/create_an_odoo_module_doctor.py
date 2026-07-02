# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateAnOdooModuleDoctor(models.Model):
    _name = 'create_an_odoo_module.doctor'
    _description = 'Doctor'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    specialization = fields.Char(
        string='Specialization',
    )
    license_number = fields.Char(
        string='License Number',
    )
