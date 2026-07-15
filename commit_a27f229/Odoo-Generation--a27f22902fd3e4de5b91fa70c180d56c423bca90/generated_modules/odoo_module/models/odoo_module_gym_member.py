# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OdooModuleGymMember(models.Model):
    _name = 'odoo_module.gym_member'
    _description = 'Gym Member'
    _rec_name = 'name'

    name = fields.Char(
        string='Member Name',
        required=True,
    )
    email = fields.Char(
        string='Email',
    )
    phone = fields.Char(
        string='Phone Number',
    )
    membership_plan_id = fields.Many2one(
        comodel_name='odoo_module.membership_plan',
        string='Membership Plan',
    )
    start_date = fields.Date(
        string='Membership Start Date',
    )
    end_date = fields.Date(
        string='Membership End Date',
    )
    is_active = fields.Boolean(
        string='Active Member',
    )
