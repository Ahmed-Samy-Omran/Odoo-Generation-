# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CreateAnOdooModuleConsultation(models.Model):
    _name = 'create_an_odoo_module.consultation'
    _description = 'Consultation/Visit'
    _rec_name = 'patient_id'

    patient_id = fields.Many2one(
        comodel_name='create_an_odoo_module.patient',
        string='Patient',
        required=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='create_an_odoo_module.doctor',
        string='Doctor',
        required=True,
    )
    consultation_date = fields.Date(
        string='Consultation Date',
        compute='_compute_consultation_date',
    )

    def _compute_consultation_date(self):
        for rec in self:
            for rec in self: rec.consultation_date = fields.Date.today()

    doctor_notes = fields.Text(
        string='Doctor Notes',
    )
    diagnosis = fields.Text(
        string='Diagnosis',
    )
