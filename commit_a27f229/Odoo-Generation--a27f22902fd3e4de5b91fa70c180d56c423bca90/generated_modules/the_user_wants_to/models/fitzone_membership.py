# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FitzoneMembership(models.Model):
    _name = 'fitzone.membership'
    _description = ''

    name = fields.Char(
        string='None',
        required=True,
    )
    member_id = fields.Many2one(
        comodel_name='None',
        string='None',
        required=True,
    )
    plan_ids = fields.Many2one(
        comodel_name='None',
        string='None',
        required=True,
    )
    start_date = fields.Date(
        string='None',
    )
    end_date = fields.Date(
        string='None',
    )
    state = fields.Char(
        string='[WARNING] Selection field state converted to Char. No selection_options provided.',
    )
