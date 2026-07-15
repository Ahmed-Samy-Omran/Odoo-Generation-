# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MyTestModuleTestModel(models.Model):
    _name = 'my_test_module.test_model'
    _description = 'Test Model'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
