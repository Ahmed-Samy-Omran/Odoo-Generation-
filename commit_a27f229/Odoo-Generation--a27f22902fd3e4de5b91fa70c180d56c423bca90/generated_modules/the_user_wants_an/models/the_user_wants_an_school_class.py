# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TheUserWantsAnSchoolClass(models.Model):
    _name = 'the_user_wants_an.school_class'
    _description = 'School Class'
    _rec_name = 'name'

    name = fields.Char(
        string='Class Name/Code',
        required=True,
    )
    capacity = fields.Integer(
        string='Capacity',
    )
    teacher_id = fields.Many2one(
        comodel_name='the_user_wants_an.teacher',
        string='Associated Teacher',
    )
    student_ids = fields.One2many(
        comodel_name='the_user_wants_an.student',
        inverse_name='class_id',
        string='Students',
    )
