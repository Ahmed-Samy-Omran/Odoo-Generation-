# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TheUserWantsAnStudent(models.Model):
    _name = 'the_user_wants_an.student'
    _description = 'Student'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    student_id = fields.Char(
        string='Student ID',
        required=True,
    )
    date_of_birth = fields.Date(
        string='Date of Birth',
    )
    contact_info = fields.Text(
        string='Contact Information',
    )
    class_id = fields.Many2one(
        comodel_name='the_user_wants_an.school_class',
        string='Class',
    )
