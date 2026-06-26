# -*- coding: utf-8 -*-
from odoo import models, fields

class GymShopProduct(models.Model):
    _name = 'gym_shop.product'
    _description = 'Products sold in the gym shop.'
    _rec_name = 'name'
    name = fields.Char(
        string='Product Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    product_type = fields.Selection(
        selection=[['protein_shake', 'Protein Shake'], ['supplement', 'Supplement'], ['other', 'Other']],
        string='Product Type',
    )
    price = fields.Float(
        string='Unit Price',
    )
    quantity_on_hand = fields.Integer(
        string='Quantity On Hand',
    )
