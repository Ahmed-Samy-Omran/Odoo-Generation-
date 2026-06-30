# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OdooModuleGymClass(models.Model):
    _name = 'odoo_module.gym_class'
    _description = 'Gym Class'
    _rec_name = 'name'

    name = fields.Char(
        string='Class Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    trainer_id = fields.Many2one(
        comodel_name='odoo_module.gym_trainer',
        string='Trainer',
    )
    schedule_datetime = fields.Datetime(
        string='Schedule Date & Time',
    )
    capacity = fields.Integer(
        string='Capacity',
    )
