# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Book'
    _rec_name = 'name'

    name = fields.Char(
        string='Book Name',
        required=True,
    )
    isbn = fields.Char(
        string='ISBN',
    )
