# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductCategory(models.Model):
    _name = 'product.category'
    _description = 'Categories for electronic products.'
    _rec_name = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
    )
    parent_id = fields.Many2one(
        comodel_name='product.category',
        string='Parent Category',
    )
