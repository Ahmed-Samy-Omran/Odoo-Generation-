# -*- coding: utf-8 -*-
from odoo import models, fields, api

class GymManagementMember(models.Model):
    _name = 'gym_management.member'
    _description = 'Gym Member'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    join_date = fields.Date(
        string='Join Date',
    )
    trainer_id = fields.Many2one(
        comodel_name='gym_management.trainer',
        string='Trainer',
    )
