# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectTaskManagementTask(models.Model):
    _name = 'project_task_management.task'
    _description = 'Project Task'
    _rec_name = 'name'

    name = fields.Char(
        string='Task Title',
        required=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
    )
    priority = fields.Selection(
        selection=[['low', 'Low'], ['medium', 'Medium'], ['high', 'High'], ['urgent', 'Urgent']],
        string='Priority',
    )
    state = fields.Selection(
        selection=[['draft', 'Draft'], ['in_progress', 'In Progress'], ['review', 'Review'], ['done', 'Done'], ['cancelled', 'Cancelled']],
        string='Status',
    )
    description = fields.Html(
        string='Description',
    )
    tag_ids = fields.Many2many(
        comodel_name='project.tags',
        relation='project_task_tags_rel',
        string='Tags',
    )
    planned_hours = fields.Float(
        string='Planned Hours',
    )
    effective_hours = fields.Float(
        string='Effective Hours',
        compute='_compute_effective_hours',
    )

    @api.depends(timesheet_ids.unit_amount)
    def _compute_effective_hours(self):
        for rec in self:
            _compute_effective_hours

    remaining_hours = fields.Float(
        string='Remaining Hours',
        compute='_compute_remaining_hours',
    )

    @api.depends(planned_hours, effective_hours)
    def _compute_remaining_hours(self):
        for rec in self:
            _compute_remaining_hours

    timesheet_ids = fields.One2many(
        comodel_name='account.analytic.line',
        inverse_name='task_id',
        string='Timesheets',
    )
    start_date = fields.Datetime(
        string='Start Date',
    )
    end_date = fields.Datetime(
        string='End Date',
    )
    color = fields.Integer(
        string='Color Index',
    )
