# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TestModel(models.Model):
    _name = 'test.model'
    _description = 'Test Model'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
