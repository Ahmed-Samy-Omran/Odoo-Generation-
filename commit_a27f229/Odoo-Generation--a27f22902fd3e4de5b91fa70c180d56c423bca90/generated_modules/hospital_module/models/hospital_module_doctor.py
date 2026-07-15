# -*- coding: utf-8 -*-
from odoo import models, fields


class HospitalModuleDoctor(models.Model):
    _name = 'hospital_module.doctor'
    _description = 'Doctor Records'
    _rec_name = 'name'


name = fields.Char(string='Doctor Name', required=True, )
specialty = fields.Char(string='Specialty', )
