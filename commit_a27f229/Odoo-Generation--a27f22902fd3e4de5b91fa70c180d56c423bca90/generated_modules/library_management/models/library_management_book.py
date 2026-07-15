# -*- coding: utf-8 -*-
from odoo import models, fields, api

class LibraryManagementBook(models.Model):
    _name = 'library_management.book'
    _description = 'Book'
    _rec_name = 'title'

    title = fields.Char(
        string='Title',
        required=True,
    )
    author = fields.Char(
        string='Author',
        required=True,
    )
    is_published = fields.Boolean(
        string='Is Published',
    )
