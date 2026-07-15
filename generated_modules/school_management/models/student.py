# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Student(models.Model):
    _name = 'student'
    _description = 'Student'
    _rec_name = 'name'

    name = fields.Char(
        string='Student Name',
        required=True,
    )
    email = fields.Char(
        string='Email',
    )
    phone = fields.Char(
        string='Phone',
    )
    date_of_birth = fields.Date(
        string='Date of Birth',
    )
    gender = fields.Selection(
        selection=[['male', 'Male'], ['female', 'Female']],
        string='Gender',
    )
    address = fields.Text(
        string='Address',
    )
    enrollment_date = fields.Date(
        string='Enrollment Date',
        required=True,
    )
    class_id = fields.Many2one(
        comodel_name='class',
        string='Class',
    )
    guardian_name = fields.Char(
        string='Guardian Name',
    )
    guardian_phone = fields.Char(
        string='Guardian Phone',
    )
