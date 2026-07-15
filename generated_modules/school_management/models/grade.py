# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Grade(models.Model):
    _name = 'grade'
    _description = 'Grade'
    _rec_name = 'name'

    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        required=True,
    )
    course_id = fields.Many2one(
        comodel_name='course',
        string='Course',
        required=True,
    )
    score = fields.Float(
        string='Score',
        required=True,
    )
    grade = fields.Char(
        string='Grade',
    )
    exam_date = fields.Date(
        string='Exam Date',
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
    )

    @api.depends(student_id.name, course_id.name)
    def _compute_name(self):
        for rec in self:
            for rec in self:
                rec.name = f"{rec.student_id.name} - {rec.course_id.name}"

