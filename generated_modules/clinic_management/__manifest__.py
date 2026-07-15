# -*- coding: utf-8 -*-
{
    'name': 'clinic_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Clinic Management System',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/clinic_management_patient_views.xml',
        'views/clinic_management_doctor_views.xml',
        'views/clinic_management_appointment_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}