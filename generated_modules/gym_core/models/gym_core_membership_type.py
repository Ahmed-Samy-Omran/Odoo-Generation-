# -*- coding: utf-8 -*-
from odoo import models, fields

class GymCoreMembershipType(models.Model):
    _name = 'gym_core.membership_type'
    _description = 'Defines different types of gym memberships.'
    _rec_name = 'name'
    name = fields.Char(
        string='Membership Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    price = fields.Float(
        string='Price',
    )
