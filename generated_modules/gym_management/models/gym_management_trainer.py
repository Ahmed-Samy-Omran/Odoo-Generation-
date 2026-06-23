# -*- coding: utf-8 -*-
from odoo import models, fields, api

class GymManagementTrainer(models.Model):
    _name = 'gym_management.trainer'
    _description = 'Gym Trainer'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    specialty = fields.Char(
        string='Specialty',
    )
    salary = fields.Float(
        string='Salary',
    )
