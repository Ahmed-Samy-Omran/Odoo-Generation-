# -*- coding: utf-8 -*-
{
    'name': 'gym_core',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Manages gym members and trainers.',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/gym_core_membership_type_views.xml',
        'views/gym_core_trainer_views.xml',
        'views/gym_core_member_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}