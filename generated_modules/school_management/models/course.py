# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Course(models.Model):
    _name = 'course'
    _description = 'Course'
    _rec_name = 'name'

    name = fields.Char(
        string='Course Name',
        required=True,
    )
    code = fields.Char(
        string='Course Code',
        required=True,
    )
    teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Teacher',
        required=True,
    )
    credit_hours = fields.Integer(
        string='Credit Hours',
    )
    description = fields.Text(
        string='Description',
    )
    grade_ids = fields.One2many(
        comodel_name='grade',
        inverse_name='course_id',
        string='Grades',
    )
