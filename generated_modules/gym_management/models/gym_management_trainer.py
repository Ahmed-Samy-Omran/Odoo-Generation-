# -*- coding: utf-8 -*-
from odoo import models, fields

class GymManagementTrainer(models.Model):
    _name = 'gym_management.trainer'
    _description = 'Gym Trainer Records'    _rec_name = 'name'
name = fields.Char(        string='Trainer Name',        required=True,    )
specialty = fields.Char(        string='Specialty',    )
salary = fields.Float(        string='Salary',    )
