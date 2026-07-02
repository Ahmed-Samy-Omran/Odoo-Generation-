# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TheUserWantsAnTeacher(models.Model):
    _name = 'the_user_wants_an.teacher'
    _description = 'Teacher'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    employee_id = fields.Char(
        string='Employee ID',
        required=True,
    )
    contact_info = fields.Text(
        string='Contact Information',
    )
    subjects_taught = fields.Text(
        string='Subjects Taught',
    )
