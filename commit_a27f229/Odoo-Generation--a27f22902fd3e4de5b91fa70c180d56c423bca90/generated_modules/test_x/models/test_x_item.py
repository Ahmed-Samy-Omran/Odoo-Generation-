# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TestXItem(models.Model):
    _name = 'test_x.item'
    _description = ''

    title = fields.Char(
        string='None',
        required=True,
    )
