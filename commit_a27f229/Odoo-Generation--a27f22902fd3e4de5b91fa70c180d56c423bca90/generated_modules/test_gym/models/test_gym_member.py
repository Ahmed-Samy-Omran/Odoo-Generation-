# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TestGymMember(models.Model):
    _name = 'test_gym.member'
    _description = 'Member'

    name = fields.Char(
        string='Name',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
    )
