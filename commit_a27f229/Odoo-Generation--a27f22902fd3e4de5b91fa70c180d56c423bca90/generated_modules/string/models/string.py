# -*- coding: utf-8 -*-
from odoo import models, fields, api

class String(models.Model):
    _name = 'string'
    _description = ''
    _rec_name = 'string'

    string = fields.String(
        string='string',
    )
