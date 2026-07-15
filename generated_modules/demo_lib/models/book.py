# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Book(models.Model):
    _name = 'book'
    _description = 'Book'
    _rec_name = 'name'

    name = fields.Char(
        string='Title',
        required=True,
    )
    isbn = fields.Char(
        string='ISBN',
    )
