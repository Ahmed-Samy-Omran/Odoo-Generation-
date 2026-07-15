# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AzayakExampleModel(models.Model):
    _name = 'azayak.example_model'
    _description = 'Example Model for Azayak'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
