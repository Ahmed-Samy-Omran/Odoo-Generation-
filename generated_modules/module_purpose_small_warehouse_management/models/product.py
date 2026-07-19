# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Product(models.Model):
    _name = 'product'
    _description = 'Handles product inventory details.'
    _rec_name = 'name'

    name = fields.Char(
        string='Product Name',
        required=True,
    )
    default_code = fields.Char(
        string='Internal Reference',
    )
    barcode = fields.Char(
        string='Barcode',
    )
    list_price = fields.Float(
        string='Sales Price',
    )
    standard_price = fields.Float(
        string='Cost',
    )
    qty_available = fields.Float(
        string='Quantity On Hand',
    )
    min_stock_level = fields.Float(
        string='Minimum Stock Level',
    )
    storage_location = fields.Char(
        string='Storage Location',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )
