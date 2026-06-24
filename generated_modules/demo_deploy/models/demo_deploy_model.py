# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DemoDeployModel(models.Model):
    _name = 'demo_deploy.model'
    _description = 'Demo Model'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
    )
