# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Appointment(models.Model):
    _name = 'appointment'
    _description = 'Dental Appointment'
    _rec_name = 'name'

    name = fields.Char(
        string='Ref',
        required=True,
    )
    patient_name = fields.Char(
        string='Patient Name',
        required=True,
    )
    date = fields.Date(
        string='Appointment Date',
    )
    procedure = fields.Selection(
        selection=[['cleaning', 'Cleaning'], ['filling', 'Filling']],
        string='Procedure',
    )
