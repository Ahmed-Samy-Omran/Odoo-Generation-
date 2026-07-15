# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductProduct(models.Model):
    _name = 'product.product'
    _description = 'Electronic products inventory management.'
    _rec_name = 'name'

    name = fields.Char(
        string='Product Name',
        required=True,
    )
    internal_reference = fields.Char(
        string='Internal Reference',
    )
    category_id = fields.Many2one(
        comodel_name='product.category',
        string='Category',
        required=True,
    )
    price = fields.Float(
        string='Price',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity Available',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    image = fields.Binary(
        string='Product Image',
    )
    barcode = fields.Char(
        string='Barcode',
    )
    active = fields.Boolean(
        string='Active',
    )
