# -*- coding: utf-8 -*-
{
    'name': 'module_purpose_a_clinic_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'A clinic management module for Odoo to handle patients, doctors, and appointments with role-based permissions and a user-friendly UI.',
    'author': 'Generated Module',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/patient_views.xml',
        'views/doctor_views.xml',
        'views/appointment_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}