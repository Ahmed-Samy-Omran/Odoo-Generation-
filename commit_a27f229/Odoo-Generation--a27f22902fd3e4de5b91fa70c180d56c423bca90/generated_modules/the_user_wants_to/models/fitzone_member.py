# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FitzoneMember(models.Model):
    _name = 'fitzone.member'
    _description = ''

    name = fields.Char(
        string='None',
        required=True,
    )
    phone = fields.Char(
        string='None',
    )
    email = fields.Char(
        string='None',
    )
    plan_id = fields.Many2one(
        comodel_name='None',
        string='None',
    )
    membership_ids = fields.One2many(
        comodel_name='None',
        inverse_name='None',
        string='None',
    )
