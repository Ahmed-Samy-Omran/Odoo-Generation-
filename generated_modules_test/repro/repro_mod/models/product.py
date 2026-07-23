# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Product(models.Model):
    _name = 'product'
    _description = ''

    name = fields.Char(
        string='Name',
        required=True,
    )
