# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HealthManagementHealthRecord(models.Model):
    _name = 'health_management.health_record'
    _description = 'Health Record'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
    )
    checkup_date = fields.Date(
        string='Checkup Date',
        required=True,
    )
    notes = fields.Text(
        string='Notes',
    )
    is_urgent = fields.Boolean(
        string='Is Urgent',
        compute='_compute_is_urgent',
    )

    @api.depends(checkup_date)
    def _compute_is_urgent(self):
        for rec in self:
            for record in self:
                if record.checkup_date:
                    delta = fields.Date.today() - record.checkup_date
                    record.is_urgent = delta.days > 30
                else:
                    record.is_urgent = False

