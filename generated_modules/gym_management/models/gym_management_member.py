# -*- coding: utf-8 -*-
from odoo import models, fields

class GymManagementMember(models.Model):
    _name = 'gym_management.member'
    _description = 'Gym Member Records'    _rec_name = 'name'
name = fields.Char(        string='Member Name',        required=True,    )
join_date = fields.Date(        string='Join Date',    )
trainer_id = fields.Many2one(        string='Assigned Trainer',        comodel_name='gym_management.trainer',    )
