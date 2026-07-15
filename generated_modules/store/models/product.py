# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Product(models.Model):
    _name = 'product'
    _description = 'Product'

    name = fields.Char(
        string='Product Name',
        required=True,
    )
    price = fields.Float(
        string='Price',
    )
    quantity = fields.Integer(
        string='Quantity',
    )
