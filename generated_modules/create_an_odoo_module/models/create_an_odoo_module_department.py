# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateAnOdooModuleDepartment(models.Model):
    _name = 'create_an_odoo_module.department'
    _description = 'Medical Department'
    _rec_name = 'name'

    name = fields.Char(
        string='Department Name',
        required=True,
    )
