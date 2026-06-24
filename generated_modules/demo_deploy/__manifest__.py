# -*- coding: utf-8 -*-
{
    'name': 'demo_deploy',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Demo Deploy Module',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/demo_deploy_demo_model_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}