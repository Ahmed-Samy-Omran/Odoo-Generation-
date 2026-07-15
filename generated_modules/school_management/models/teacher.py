# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Teacher(models.Model):
    _name = 'teacher'
    _description = 'Teacher'
    _rec_name = 'name'

    name = fields.Char(
        string='Teacher Name',
        required=True,
    )
    email = fields.Char(
        string='Email',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
    )
    specialization = fields.Char(
        string='Specialization',
    )
    hire_date = fields.Date(
        string='Hire Date',
        required=True,
    )
    salary = fields.Float(
        string='Salary',
    )
    course_ids = fields.One2many(
        comodel_name='course',
        inverse_name='teacher_id',
        string='Courses',
    )
