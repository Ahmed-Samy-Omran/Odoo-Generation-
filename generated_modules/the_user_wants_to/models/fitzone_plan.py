# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FitzonePlan(models.Model):
    _name = 'fitzone.plan'
    _description = ''

    name = fields.Char(
        string='None',
        required=True,
    )
    price = fields.Float(
        string='None',
    )
    duration_days = fields.Integer(
        string='None',
    )
