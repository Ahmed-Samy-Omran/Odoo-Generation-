# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FitzoneMember(models.Model):
    _name = 'fitzone.member'
    _description = 'Gym Member'
    _rec_name = 'name'

    name = fields.Char(
        string='Full Name',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
    )
    email = fields.Char(
        string='Email',
    )
    plan_id = fields.Many2one(
        comodel_name='fitzone.plan',
        string='Subscription Plan',
    )
    membership_ids = fields.One2many(
        comodel_name='fitzone.membership',
        inverse_name='member_id',
        string='Memberships',
    )
