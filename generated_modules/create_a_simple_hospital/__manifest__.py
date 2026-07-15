# -*- coding: utf-8 -*-
{
    'name': 'create_a_simple_hospital',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Simple Hospital Management',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/create_a_simple_hospital_patient_views.xml',
        'views/create_a_simple_hospital_doctor_views.xml',
        'views/create_a_simple_hospital_appointment_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}