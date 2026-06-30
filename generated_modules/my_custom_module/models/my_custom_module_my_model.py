# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MyCustomModuleMyModel(models.Model):
    _name = 'my_custom_module.my_model'
    _description = 'My Custom Model'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
