# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectManagementProject(models.Model):
    _name = 'project_management.project'
    _description = 'Project'
    _rec_name = 'name'

    name = fields.Char(
        string='Project Name',
        required=True,
    )
    code = fields.Char(
        string='Project Code',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
    )
    end_date = fields.Date(
        string='End Date',
    )
    state = fields.Selection(
        selection=[['draft', 'Draft'], ['active', 'Active'], ['on_hold', 'On Hold'], ['completed', 'Completed'], ['cancelled', 'Cancelled']],
        string='Status',
        required=True,
    )
    manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Project Manager',
        required=True,
    )
    team_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='project_management_project_employeerel',
        string='Team Members',
    )
    task_ids = fields.One2many(
        comodel_name='project_management.task',
        inverse_name='project_id',
        string='Tasks',
    )
    milestone_ids = fields.One2many(
        comodel_name='project_management.milestone',
        inverse_name='project_id',
        string='Milestones',
    )
    budget = fields.Float(
        string='Budget',
    )
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
    )

    @api.depends(task_ids, task_ids.estimated_hours)
    def _compute_total_hours(self):
        for rec in self:
            for record in self:
                record.total_hours = sum(record.task_ids.mapped('estimated_hours'))

    progress = fields.Float(
        string='Progress (%)',
        compute='_compute_progress',
    )

    @api.depends(task_ids, task_ids.state)
    def _compute_progress(self):
        for rec in self:
            for record in self:
                total_tasks = len(record.task_ids)
                if total_tasks:
                    completed = len(record.task_ids.filtered(lambda t: t.state == 'done'))
                    record.progress = (completed / total_tasks) * 100
                else:
                    record.progress = 0.0

    color = fields.Integer(
        string='Color Index',
    )
    active = fields.Boolean(
        string='Active',
    )
