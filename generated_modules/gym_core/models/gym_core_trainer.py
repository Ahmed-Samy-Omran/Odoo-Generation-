# -*- coding: utf-8 -*-
from odoo import models, fields

class GymCoreTrainer(models.Model):
    _name = 'gym_core.trainer'
    _description = 'Manages gym trainers.'
    _rec_name = 'name'
    name = fields.Char(
        string='Trainer Name',
        required=True,
    )
    email = fields.Char(
        string='Email',
    )
    phone = fields.Char(
        string='Phone',
    )
    specialty = fields.Char(
        string='Specialty',
    )
    member_ids = fields.One2many(
        comodel_name='gym_core.member',
        inverse_name='trainer_id',
        string='Assigned Members',
    )
