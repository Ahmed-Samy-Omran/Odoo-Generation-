# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FitzoneMembership(models.Model):
    _name = 'fitzone.membership'
    _description = 'Member Subscription'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True,
    )
    member_id = fields.Many2one(
        comodel_name='fitzone.member',
        string='Member',
        required=True,
    )
    plan_id = fields.Many2one(
        comodel_name='fitzone.plan',
        string='Plan',
        required=True,
    )
    start_date = fields.Date(
        string='Start Date',
    )
    end_date = fields.Date(
        string='End Date',
    )
    state = fields.Selection(
        selection=[['active', 'Active'], ['expired', 'Expired'], ['cancelled', 'Cancelled']],
        string='Status',
    )
