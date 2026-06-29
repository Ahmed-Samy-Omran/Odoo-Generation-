# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OdooModuleExampleModel(models.Model):
    _name = 'odoo_module.example_model'
    _description = 'Example Model for Odoo Module'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
