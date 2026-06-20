# -*- coding: utf-8 -*-
from odoo import models, fields

class TodoTaskManagementTodoTask(models.Model):
    _name = 'todo_task_management.todo_task'
    _description = 'Todo Task'
    _rec_name = 'name'
    name = fields.Char(
        string='Task Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    dead_line = fields.Date(
        string='Deadline',
    )
    status = fields.Selection(
        selection=[['draft', 'Draft'], ['in_progress', 'In Progress'], ['done', 'Done']],
        string='Status',
    )
