# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TheUserWantsAnSchedule(models.Model):
    _name = 'the_user_wants_an.schedule'
    _description = 'Schedule Entry'
    _rec_name = 'name'

    name = fields.Char(
        string='Schedule Entry Name',
        compute='_compute_name',
    )

    @api.depends(class_id, course_id, day_of_week)
    def _compute_name(self):
        for rec in self:
            for rec in self:
                rec.name = f'{rec.class_id.name} - {rec.course_id.name} ({rec.day_of_week})' if rec.class_id and rec.course_id else ''

    class_id = fields.Many2one(
        comodel_name='the_user_wants_an.school_class',
        string='Class',
        required=True,
    )
    course_id = fields.Many2one(
        comodel_name='the_user_wants_an.course',
        string='Course',
        required=True,
    )
    teacher_id = fields.Many2one(
        comodel_name='the_user_wants_an.teacher',
        string='Teacher',
        required=True,
    )
    start_time = fields.Float(
        string='Start Time',
    )
    end_time = fields.Float(
        string='End Time',
    )
    day_of_week = fields.Selection(
        selection=[['monday', 'Monday'], ['tuesday', 'Tuesday'], ['wednesday', 'Wednesday'], ['thursday', 'Thursday'], ['friday', 'Friday'], ['saturday', 'Saturday'], ['sunday', 'Sunday']],
        string='Day of the Week',
    )
    classroom = fields.Char(
        string='Classroom',
    )
