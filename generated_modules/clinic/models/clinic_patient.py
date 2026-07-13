from odoo import models, fields


class ClinicPatient(models.Model):
    _name = 'clinic.customer'
    _description = 'Clinic Patient'

    name = fields.Char(string='Name', required=True)
    dob = fields.Date(string='Date of Birth')
    note = fields.Text(string='Notes')
