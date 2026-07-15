# -*- coding: utf-8 -*-
{
    'name': 'create_an_odoo_module',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'A mini hospital management system.',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/create_an_odoo_module_patient_views.xml',
        'views/create_an_odoo_module_doctor_views.xml',
        'views/create_an_odoo_module_department_views.xml',
        'views/create_an_odoo_module_appointment_views.xml',
        'views/create_an_odoo_module_consultation_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}