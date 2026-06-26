# -*- coding: utf-8 -*-
{
    'name': 'hospital_module',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Module for managing hospital patients and doctors',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/hospital_module_patient_views.xml',
        'views/hospital_module_doctor_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}