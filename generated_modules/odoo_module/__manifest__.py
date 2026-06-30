# -*- coding: utf-8 -*-
{
    'name': 'odoo_module',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'نظام لادارة الجيم',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/odoo_module_membership_plan_views.xml',
        'views/odoo_module_gym_member_views.xml',
        'views/odoo_module_gym_trainer_views.xml',
        'views/odoo_module_gym_class_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}