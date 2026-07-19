# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Patient(models.Model):
    _name = 'patient'
    _description = ''

    name = fields.Char(
        string='None',
        required=True,
    )
