# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TestModuleExample(models.Model):
    _name = 'test_module.example'
    _description = 'Example Model'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
    )
    date_field = fields.Date(
        string='Date',
    )
    datetime_field = fields.Datetime(
        string='Date and Time',
    )
    integer_field = fields.Integer(
        string='Integer Value',
    )
    float_field = fields.Float(
        string='Float Value',
    )
    selection_field = fields.Selection(
        selection=[['option1', 'Option 1'], ['option2', 'Option 2'], ['option3', 'Option 3']],
        string='Selection',
    )
    many2one_field = fields.Many2one(
        comodel_name='res.partner',
        string='Many2One Relation',
    )
    one2many_field = fields.One2many(
        comodel_name='test_module.example_line',
        inverse_name='example_id',
        string='One2Many Relation',
    )
    many2many_field = fields.Many2many(
        comodel_name='res.users',
        relation='test_module_example_users_rel',
        string='Many2Many Relation',
    )
