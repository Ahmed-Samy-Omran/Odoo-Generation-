# -*- coding: utf-8 -*-
from odoo import models, fields

class GymCoreMember(models.Model):
    _name = 'gym_core.member'
    _description = 'Manages gym members.'
    _rec_name = 'name'
    name = fields.Char(
        string='Member Name',
        required=True,
    )
    email = fields.Char(
        string='Email',
    )
    phone = fields.Char(
        string='Phone',
    )
    registration_date = fields.Date(
        string='Registration Date',
    )
    membership_type_id = fields.Many2one(
        comodel_name='gym_core.membership_type',
        string='Membership Type',
    )
    trainer_id = fields.Many2one(
        comodel_name='gym_core.trainer',
        string='Assigned Trainer',
    )
