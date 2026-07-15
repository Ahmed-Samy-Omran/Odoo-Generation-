# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TheUserWantsAnCourse(models.Model):
    _name = 'the_user_wants_an.course'
    _description = 'Course'
    _rec_name = 'name'

    name = fields.Char(
        string='Course Name',
        required=True,
    )
    course_code = fields.Char(
        string='Course Code',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
