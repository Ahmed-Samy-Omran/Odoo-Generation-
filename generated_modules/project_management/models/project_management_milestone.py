# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectManagementMilestone(models.Model):
    _name = 'project_management.milestone'
    _description = 'Milestone'
    _rec_name = 'name'

    name = fields.Char(
        string='Milestone Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    project_id = fields.Many2one(
        comodel_name='project_management.project',
        string='Project',
        required=True,
    )
    target_date = fields.Date(
        string='Target Date',
        required=True,
    )
    state = fields.Selection(
        selection=[['pending', 'Pending'], ['in_progress', 'In Progress'], ['achieved', 'Achieved'], ['missed', 'Missed']],
        string='Status',
        required=True,
    )
    task_ids = fields.One2many(
        comodel_name='project_management.task',
        inverse_name='milestone_id',
        string='Tasks',
    )
    completion_rate = fields.Float(
        string='Completion Rate (%)',
        compute='_compute_completion_rate',
    )

    @api.depends(task_ids, task_ids.state)
    def _compute_completion_rate(self):
        for rec in self:
            for record in self:
                total_tasks = len(record.task_ids)
                if total_tasks:
                    completed = len(record.task_ids.filtered(lambda t: t.state == 'done'))
                    record.completion_rate = (completed / total_tasks) * 100
                else:
                    record.completion_rate = 0.0

    active = fields.Boolean(
        string='Active',
    )
