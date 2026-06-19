# -*- coding: utf-8 -*-
{
    'name': 'gym_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Module for managing gym trainers and members',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/gym_management_trainer_views.xml',
        'views/gym_management_member_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}