# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OdooModuleGymTrainer(models.Model):
    _name = 'odoo_module.gym_trainer'
    _description = 'Gym Trainer'
    _rec_name = 'name'

    name = fields.Char(
        string='Trainer Name',
        required=True,
    )
    email = fields.Char(
        string='Email',
    )
    phone = fields.Char(
        string='Phone Number',
    )
    specialization = fields.Char(
        string='Specialization',
    )
