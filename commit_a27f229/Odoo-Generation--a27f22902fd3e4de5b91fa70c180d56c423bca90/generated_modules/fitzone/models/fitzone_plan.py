# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FitzonePlan(models.Model):
    _name = 'fitzone.plan'
    _description = 'Subscription Plan'
    _rec_name = 'name'

    name = fields.Char(
        string='Plan Name',
        required=True,
    )
    price = fields.Float(
        string='Price',
    )
    duration_days = fields.Integer(
        string='Duration (days)',
    )
