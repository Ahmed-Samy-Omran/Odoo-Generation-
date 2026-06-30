# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OdooModuleMembershipPlan(models.Model):
    _name = 'odoo_module.membership_plan'
    _description = 'Membership Plan'
    _rec_name = 'name'

    name = fields.Char(
        string='Plan Name',
        required=True,
    )
    price = fields.Float(
        string='Price',
    )
    duration_days = fields.Integer(
        string='Duration (Days)',
    )
    description = fields.Text(
        string='Description',
    )
