# -*- coding: utf-8 -*-
{
    'name': 'custom_hospital',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Module for managing hospital patients and doctors',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',        'views/hospital.patient_views.xml',        'views/hospital.doctor_views.xml',    ],
    'installable': True,
    'application': False,
}