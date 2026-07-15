# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Class(models.Model):
    _name = 'class'
    _description = 'Class'
    _rec_name = 'name'

    name = fields.Char(
        string='Class Name',
        required=True,
    )
    level = fields.Integer(
        string='Level',
    )
    section = fields.Char(
        string='Section',
    )
    capacity = fields.Integer(
        string='Capacity',
    )
    teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Class Teacher',
    )
    room_number = fields.Char(
        string='Room Number',
    )
    student_ids = fields.One2many(
        comodel_name='student',
        inverse_name='class_id',
        string='Students',
    )
