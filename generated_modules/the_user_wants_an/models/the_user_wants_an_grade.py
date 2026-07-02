# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TheUserWantsAnGrade(models.Model):
    _name = 'the_user_wants_an.grade'
    _description = 'Grade'
    _rec_name = 'name'

    name = fields.Char(
        string='Grade Reference',
        compute='_compute_name',
    )

    @api.depends(student_id, course_id)
    def _compute_name(self):
        for rec in self:
            for rec in self:
                rec.name = f'{rec.student_id.name} - {rec.course_id.name}' if rec.student_id and rec.course_id else ''

    student_id = fields.Many2one(
        comodel_name='the_user_wants_an.student',
        string='Student',
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
    grade_value = fields.Char(
        string='Grade Value',
    )
    grading_date = fields.Date(
        string='Grading Date',
        required=True,
    )
