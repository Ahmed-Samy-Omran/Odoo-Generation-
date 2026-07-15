# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectManagementTask(models.Model):
    _name = 'project_management.task'
    _description = 'Task'
    _rec_name = 'name'

    name = fields.Char(
        string='Task Name',
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
    milestone_id = fields.Many2one(
        comodel_name='project_management.milestone',
        string='Milestone',
    )
    assigned_to_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Assigned To',
    )
    priority = fields.Selection(
        selection=[['low', 'Low'], ['medium', 'Medium'], ['high', 'High'], ['urgent', 'Urgent']],
        string='Priority',
        required=True,
    )
    state = fields.Selection(
        selection=[['todo', 'To Do'], ['in_progress', 'In Progress'], ['review', 'In Review'], ['done', 'Done'], ['blocked', 'Blocked']],
        string='Status',
        required=True,
    )
    start_date = fields.Date(
        string='Start Date',
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
    )
    estimated_hours = fields.Float(
        string='Estimated Hours',
    )
    actual_hours = fields.Float(
        string='Actual Hours',
    )
    completion_percentage = fields.Integer(
        string='Completion %',
    )
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
    )

    @api.depends(due_date, state)
    def _compute_is_overdue(self):
        for rec in self:
            from datetime import date
            for record in self:
                if record.due_date and record.state not in ['done']:
                    record.is_overdue = record.due_date < date.today()
                else:
                    record.is_overdue = False

    color = fields.Integer(
        string='Color Index',
    )
    active = fields.Boolean(
        string='Active',
    )
